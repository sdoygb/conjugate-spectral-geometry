"""
stream.py — 流式生成模块
从 geometry_ai_server_v5_12.py 提取
包含：stream_generate 函数
"""

import hashlib
import json
import re
import time
import uuid
from typing import List, Dict, Any

import openai

from config import GAI_API_KEY, GAI_BASE_URL, GAI_MODEL, logger, get_provider_for_model
from tools import execute_tool_call, reset_view_article_count, reset_tool_session, set_session_mode, init_session_mode, _CODING_KEYWORDS
from guardian import ReadTracker

# API 调用重试配置
API_MAX_RETRIES = 3
API_RETRY_DELAY = 2  # 秒


def _is_retryable_error(e: Exception) -> bool:
    """判断是否为可重试的网络/API 错误"""
    retryable_keywords = [
        'TransferEncodingError', 'IncompleteRead', 'ConnectionResetError',
        'ConnectionError', 'RemoteProtocolError', 'timeout', 'timed out',
        'Not enough data', 'Connection aborted', 'BrokenPipeError',
        'APIConnectionError', 'APIStatusError', 'InternalServerError',
        'ServiceUnavailableError', 'RateLimitError',
    ]
    err_str = str(e).lower()
    for kw in retryable_keywords:
        if kw.lower() in err_str:
            return True
    # HTTP 429/500/502/503/504 都可重试
    if hasattr(e, 'status_code') and e.status_code in (429, 500, 502, 503, 504):
        return True
    return False


def _extract_derivation_state(messages: List[Dict], max_items: int = 6) -> str:
    """token 节省整改 B：从对话消息里提取「推导状态」（已确认结论/已读文章/待办）。
    规则式免费提取（不调模型）：
    - assistant 纯文本消息：取含结论性词（确认/得到/发现/因此/结论/=）的短句
    - 已读文章：从 tool 结果里的「文件: xxx」提取
    返回注入用的 system 文本；无内容返回空串。"""
    import re as _re_ds
    _concl_pat = _re_ds.compile(r'([^。\n]{6,80}(?:确认|得到|发现|因此|结论|已|成立|等于|推出|验证)[^。\n]{0,60})')
    _finds = []
    _read_files = []
    for _m in messages[-12:]:  # 只看最近 12 条（避免稀释）
        _r = _m.get("role")
        _c = str(_m.get("content") or "")
        if _r == "assistant" and _c.strip():
            for _mt in _concl_pat.finditer(_c):
                _s = _mt.group(1).strip()
                if len(_s) >= 6 and _s not in _finds:
                    _finds.append(_s)
                    if len(_finds) >= max_items:
                        break
        elif _r == "tool":
            _mf = _re_ds.search(r'文件: ([^\s(]+\.md)', _c)
            if _mf and _mf.group(1) not in _read_files:
                _read_files.append(_mf.group(1))
    if not _finds and not _read_files:
        return ""
    _lines = ["【推导状态（自动提取，供续推参考）】"]
    if _finds:
        _lines.append("已确认/得出：")
        _lines += [f"- {_f}" for _f in _finds]
    if _read_files:
        _lines.append("已读取文章：")
        _lines += [f"- {_f}" for _f in _read_files[:5]]
    _lines.append("请基于以上已确认内容继续推进推导，不要重复检索或重读已确认的部分。")
    return "\n".join(_lines)


def parse_dsml_tool_calls(text: str) -> list:
    """
    解析 DeepSeek 模型输出的 DSML 格式工具调用。
    DSML 格式示例：
        <｜｜DSML｜｜tool_calls>
        <｜｜DSML｜｜invoke name="view_article">
        <｜｜DSML｜｜parameter name="filename" string="true">0.3.1_量纲桥_CN_260626.6.md</｜｜DSML｜｜parameter>
        </｜｜DSML｜｜invoke>
        </｜｜DSML｜｜tool_calls>

    返回与 OpenAI tool_calls 格式兼容的列表。
    """
    if not text or 'DSML' not in text:
        return []

    tool_calls = []
    # 匹配所有 invoke 块
    invoke_pattern = re.compile(
        r'<｜｜DSML｜｜invoke\s+name="([^"]+)">(.*?)</｜｜DSML｜｜invoke>',
        re.DOTALL
    )

    for match in invoke_pattern.finditer(text):
        func_name = match.group(1)
        params_block = match.group(2)

        # 解析参数
        args = {}
        param_pattern = re.compile(
            r'<｜｜DSML｜｜parameter\s+name="([^"]+)"\s+(?:string="[^"]*")?\s*>(.*?)</｜｜DSML｜｜parameter>',
            re.DOTALL
        )
        for param_match in param_pattern.finditer(params_block):
            param_name = param_match.group(1)
            param_value = param_match.group(2).strip()

            # 尝试转换为数字
            try:
                if '.' in param_value:
                    param_value = float(param_value)
                else:
                    param_value = int(param_value)
            except (ValueError, TypeError):
                pass

            # 处理布尔值
            if param_value == 'true':
                param_value = True
            elif param_value == 'false':
                param_value = False

            args[param_name] = param_value

        tool_calls.append({
            "id": f"dsml_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {
                "name": func_name,
                "arguments": json.dumps(args, ensure_ascii=False)
            }
        })

    return tool_calls


def stream_generate(data: Dict[str, Any], eta_before: float, final_messages: List[Dict],
                    api_params: Dict[str, Any], vector_kb=None) -> Any:
    # 多模型路由：根据请求中的 model 字段选择提供商
    request_model = api_params.get("model", GAI_MODEL)
    _supports_thinking = any(p in request_model.lower() for p in ['deepseek', 'qwen', 'doubao'])
    base_url, api_key = get_provider_for_model(request_model)
    # 禁代理直连 + 加长超时（避免沙箱代理/牛来慢响应导致 Request timed out）
    import httpx as _httpx
    client = openai.OpenAI(api_key=api_key, base_url=base_url, http_client=_httpx.Client(trust_env=False), timeout=300.0, max_retries=1)
    max_tool_rounds = 25
    seen_calls = set()  # 防止重复调用
    _compact_done = False  # 标记是否发生过上下文压缩
    _total_tool_calls = {}  # 全局累计工具调用次数（跨轮次）
    _total_tool_input_tokens = 0  # 全局累计工具结果 token 数（估算）
    _total_view_chars = 0  # 全局累计 view_article 读取的原始文章字符数
    _read_tracker = ReadTracker(repeat_threshold=3)  # 护法：重复读取追踪器
    reset_view_article_count()  # 每次请求重置 view_article 调用计数
    _resp_id = f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
    # token 节省整改：会话级工具状态（calculate_math 命名空间 / shell 预算 / 已读区间）
    # 优先用请求携带的 session_id（与 server.py 的 _derive_session_id 同源），退化为请求级唯一键
    _tool_sid = ""
    for _k in ('session_id', 'chat_id', 'conversation_id'):
        _v = data.get(_k)
        if _v and isinstance(_v, str) and len(_v) > 4:
            _tool_sid = _v
            break
    if not _tool_sid:
        _meta = data.get('metadata', {}) or data.get('meta', {}) or {}
        for _k in ('session_id', 'chat_id', 'conversation_id'):
            _v = _meta.get(_k)
            if _v and isinstance(_v, str) and len(_v) > 4:
                _tool_sid = _v
                break
    if not _tool_sid:
        _tool_sid = f"stream:{_resp_id}"
    # token 节省整改 A：按查询内容初判任务模式（编程类放宽 shell 探索预算，仅首次生效）
    try:
        _query_txt = ""
        for _m in (data.get('messages') or []):
            if isinstance(_m, dict) and _m.get('role') == 'user':
                _c = _m.get('content') or ''
                if isinstance(_c, str):
                    _query_txt += _c + ' '
        if any(k in _query_txt.lower() for k in _CODING_KEYWORDS):
            init_session_mode(_tool_sid, 'coding')
        else:
            init_session_mode(_tool_sid, 'derive')
    except Exception:
        pass
    _created = int(time.time())
    _model = data.get('model', GAI_MODEL)
    _usage_info = {}
    _cache_accum = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                    "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 0}

    def _sse_chunk(delta: dict, finish_reason: str = None, usage: dict = None):
        """生成符合 OpenAI 规范的 SSE chunk"""
        chunk = {
            "id": _resp_id,
            "object": "chat.completion.chunk",
            "created": _created,
            "model": _model,
            "choices": [{
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason
            }]
        }
        if usage:
            chunk["usage"] = usage
        # finish_reason 为 None 时不包含该字段（OpenAI 规范）
        if finish_reason is None:
            chunk["choices"][0].pop("finish_reason")
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    def _sse_error(message: str):
        """生成符合 OpenAI 规范的 SSE 错误 chunk"""
        err = {
            "error": {
                "message": message,
                "type": "server_error",
                "param": None,
                "code": None
            }
        }
        return f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    def _stream_text(params):
        """真正流式调用 AI模型，逐 token 透传给客户端（含重试）"""
        params["stream"] = True
        last_error = None
        for _attempt in range(API_MAX_RETRIES):
            try:
                stream = client.chat.completions.create(**params)
                text_buf = ""
                fr = "stop"
                # DSML 过滤状态
                dsml_depth = 0  # 嵌套深度计数
                dsml_buffer = ""  # 缓冲区，用于检测跨 token 的 DSML 标签
                dsml_tag_pattern = re.compile(r'<｜｜DSML｜｜')
                dsml_pending = ""  # 待透传的文本（等待确认不是 DSML 的一部分）
                yield _sse_chunk({"role": "assistant"})
                for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            text_buf += delta.content
                            dsml_buffer += delta.content
                            
                            # 如果在 DSML 块内
                            if dsml_depth > 0:
                                open_tags = len(dsml_tag_pattern.findall(dsml_buffer))
                                close_tags = dsml_buffer.count('</｜｜DSML｜｜')
                                dsml_depth = open_tags - close_tags
                                if dsml_depth <= 0:
                                    dsml_buffer = ""
                                    dsml_depth = 0
                                continue
                            
                            # 检查缓冲区中是否出现 DSML 标签
                            if '<｜｜DSML｜｜' in dsml_buffer:
                                # 找到 DSML 标签，计算深度
                                open_tags = len(dsml_tag_pattern.findall(dsml_buffer))
                                close_tags = dsml_buffer.count('</｜｜DSML｜｜')
                                dsml_depth = open_tags - close_tags
                                
                                # 透传 DSML 标签之前的正常文本
                                dsml_idx = dsml_buffer.find('<｜｜DSML｜｜')
                                safe_text = dsml_buffer[:dsml_idx]
                                if safe_text:
                                    yield _sse_chunk({"content": safe_text})
                                
                                if dsml_depth <= 0:
                                    # 自闭合标签，清空
                                    dsml_buffer = ""
                                    dsml_depth = 0
                                continue
                            
                            # 安全透传：保留最近 20 个字符作为滑动窗口
                            # 如果缓冲区超过 20 字符且没有 DSML 标签，透传前面的部分
                            if len(dsml_buffer) > 20:
                                safe_len = len(dsml_buffer) - 20
                                safe_text = dsml_buffer[:safe_len]
                                dsml_buffer = dsml_buffer[safe_len:]
                                if safe_text:
                                    yield _sse_chunk({"content": safe_text})
                        cfr = getattr(chunk.choices[0], 'finish_reason', None)
                        if cfr:
                            fr = cfr
                    if hasattr(chunk, 'usage') and chunk.usage:
                        nonlocal _usage_info
                        _usage_info = {
                            "prompt_tokens": chunk.usage.prompt_tokens or 0,
                            "completion_tokens": chunk.usage.completion_tokens or 0,
                            "total_tokens": chunk.usage.total_tokens or 0,
                            "prompt_cache_hit_tokens": getattr(chunk.usage, 'prompt_cache_hit_tokens', 0) or 0,
                            "prompt_cache_miss_tokens": getattr(chunk.usage, 'prompt_cache_miss_tokens', 0) or 0
                        }
                        _cache_accum["prompt_tokens"] += _usage_info["prompt_tokens"]
                        _cache_accum["completion_tokens"] += _usage_info["completion_tokens"]
                        _cache_accum["total_tokens"] += _usage_info["total_tokens"]
                        _cache_accum["prompt_cache_hit_tokens"] += _usage_info["prompt_cache_hit_tokens"]
                        _cache_accum["prompt_cache_miss_tokens"] += _usage_info["prompt_cache_miss_tokens"]
                # 透传剩余的安全缓冲区（非 DSML 内容）
                if dsml_buffer and dsml_depth <= 0:
                    # 最终检查：移除任何残留的 DSML 片段
                    dsml_buffer = re.sub(r'<｜｜[^>]*>', '', dsml_buffer)
                    dsml_buffer = re.sub(r'</｜｜[^>]*>', '', dsml_buffer)
                    if dsml_buffer.strip():
                        yield _sse_chunk({"content": dsml_buffer})
                    dsml_buffer = ""
                # 最终检查：如果 text_buf 中有 DSML 残留，清理后输出
                if '<｜｜' in text_buf:
                    cleaned = re.sub(r'<｜｜[^>]*>.*?</｜｜[^>]*>', '', text_buf, flags=re.DOTALL)
                    cleaned = re.sub(r'<｜｜[^>]*>', '', cleaned)
                    cleaned = re.sub(r'</｜｜[^>]*>', '', cleaned)
                    # 只输出被清理的部分（之前已安全输出的部分不再重复）
                    if cleaned.strip() and cleaned.strip() != text_buf.strip():
                        # text_buf 中被过滤的 DSML 内容后可能有正常文本，追加输出
                        after_dsml = re.split(r'</｜｜[^>]*>', text_buf)[-1]
                        after_dsml = re.sub(r'<｜｜[^>]*>', '', after_dsml)
                        if after_dsml.strip():
                            yield _sse_chunk({"content": after_dsml})
                    logger.warning(f"[DSML-FILTER] text_buf 中 DSML 已清理，原始len={len(text_buf)}")
                yield _sse_chunk({}, fr, usage=_cache_accum if _cache_accum["prompt_tokens"] > 0 else None)
                yield "data: [DONE]\n\n"
                try:
                    reset_tool_session(_tool_sid)  # token 节省整改：清理会话级工具状态
                except Exception:
                    pass
                return  # 成功完成，退出重试循环
            except Exception as e:
                last_error = e
                if _is_retryable_error(e) and _attempt < API_MAX_RETRIES - 1:
                    logger.warning(f"[STREAM-RETRY] _stream_text 第{_attempt+1}次失败: {e}，{API_RETRY_DELAY}秒后重试...")
                    yield _sse_chunk({"content": f"\n\n⏳ 连接中断，正在重试 ({_attempt+1}/{API_MAX_RETRIES})...\n"})
                    time.sleep(API_RETRY_DELAY)
                    continue
                else:
                    logger.error(f"[STREAM] _stream_text 最终失败: {e}")
                    break
        # 所有重试都失败
        yield _sse_error(f"生成错误（已重试{API_MAX_RETRIES}次）: {last_error}")
        yield "data: [DONE]\n\n"

    for _round in range(max_tool_rounds):
        # ---- 上下文压缩：工具链消息累积超过阈值时，浓缩早期轮次 ----
        _COMPACT_THRESHOLD = 18000  # 字符数（token 节省整改：阈值 20000→18000，更早触发）
        _COMPACT_KEEP_RECENT = 2    # 保留最近 2 轮完整历史（token 节省整改：3→2，压缩更彻底）
        _total_chars = sum(len(str(m.get("content") or "")) + len(str(m.get("tool_calls") or "")) for m in final_messages)
        if _total_chars > _COMPACT_THRESHOLD:
            _asst_tc_idx = [i for i, m in enumerate(final_messages)
                           if m.get("role") == "assistant" and m.get("tool_calls")]
            if len(_asst_tc_idx) > _COMPACT_KEEP_RECENT:
                _cut = _asst_tc_idx[-_COMPACT_KEEP_RECENT]
                _base = []
                _parts = []
                _read_manifest = []  # token 节省整改：已读文章清单（防压缩后模型"失忆"重复读）
                _sys_compacted = False  # token 节省整改：system 参考资料块已骨架化
                for _i in range(_cut):
                    _m = final_messages[_i]
                    _r = _m.get("role")
                    if _r in ("system", "user"):
                        # token 节省整改 2a：system 里的【参考资料】注入块是上下文大头
                        # （实测 system 16747-20751 字符 vs user 仅 47-64），压缩时骨架化：
                        # 保留系统身份/纪律指令，参考资料压缩为文章名清单（仅首条 system 完整保留）
                        _c = str(_m.get("content") or "")
                        if _r == "system" and not _sys_compacted and "【参考资料" in _c:
                            _head, _sep, _tail = _c.partition("【参考资料")
                            # 提取参考资料块里的文章标题行，只保留每行开头 100 字符（文章名/编号）
                            _ref_block = _tail.split("【当前状态】")[0] if "【当前状态】" in _tail else _tail[:20000]
                            _ref_lines = [ln.strip() for ln in _ref_block.splitlines()
                                          if ln.strip() and len(ln.strip()) > 5][:40]
                            _ref_titles = [ln[:100] for ln in _ref_lines[:25]]
                            _sys_c = _head + "【参考资料（已压缩，仅保留文章标题索引；如需原文请用 view_article 按文件名读取）】\n" + "\n".join(_ref_titles)
                            # 保留【当前状态】及之后的部分（状态/语气/索引警告等）
                            if "【当前状态】" in _tail:
                                _sys_c += "\n【当前状态】" + _tail.split("【当前状态】", 1)[1]
                            _base.append({"role": "system", "content": _sys_c})
                            _sys_compacted = True
                            logger.info(f"[TOOL-COMPACT] system 参考资料骨架化: {len(_c)}→{len(_sys_c)} 字符")
                        else:
                            _base.append(_m)
                    elif _r == "tool":
                        _c = str(_m.get("content") or "")
                        # 提取已读文章信息（view_article 结果形如 "文件: xxx (共N字符, 位置: a-b)"）
                        _m_file = re.search(r'文件: ([^\s(]+)', _c)
                        _m_pos = re.search(r'位置: (\d+)-(\d+)', _c)
                        if _m_file:
                            _read_manifest.append(
                                f"{_m_file.group(1)}[{_m_pos.group(1)}-{_m_pos.group(2)}]" if _m_pos else _m_file.group(1)
                            )
                        _first = _c.split("\n")[0][:200]
                        if _first:
                            _parts.append(_first)
                    elif _r == "assistant" and (_m.get("content") or "").strip():
                        _parts.append("asst:" + str(_m.get("content"))[:200])
                if _parts:
                    _base.append({"role": "assistant",
                                 "content": "[上下文压缩：前述工具链关键产出] " + "; ".join(_parts)})
                # token 节省整改：注入已读文章清单，防止模型压缩后重复读取已读内容
                if _read_manifest:
                    _base.append({
                        "role": "user",
                        "content": "【已读文章清单（压缩保留）】本会话已读取过以下文章片段，"
                                   "不要重复读取相同内容：\n- " + "\n- ".join(_read_manifest[:30])
                    })
                final_messages[:] = _base + final_messages[_cut:]
                # 压缩后处理 reasoning_content：
                # 思考模式模型（DeepSeek/Qwen）要求所有 assistant 消息都带 reasoning_content，
                # 非思考模式模型则删除该字段避免 API 报错
                _compact_done = True
                api_params.pop("reasoning_effort", None)
                for _m in final_messages:
                    if _m.get("role") == "assistant":
                        if _supports_thinking and "reasoning_content" not in _m:
                            _m["reasoning_content"] = ""
                        elif not _supports_thinking and "reasoning_content" in _m:
                            del _m["reasoning_content"]
                logger.info(f"[TOOL-COMPACT] 第{_round+1}轮: 消息 {_total_chars}→{sum(len(str(m.get('content') or '')) for m in final_messages)} 字符，压缩 {len(_asst_tc_idx)-_COMPACT_KEEP_RECENT} 轮早期历史，已读清单 {len(_read_manifest)} 项")

        # 每轮调用前彻底清洗消息（DeepSeek/Qwen 兼容）
        # 策略：JSON 序列化/反序列化，只保留 OpenAI 标准字段
        _clean_msgs = []
        for msg in final_messages:
            _clean = {}
            _clean["role"] = msg.get("role", "user")
            # content: 确保是字符串（DeepSeek 不接受 list 格式的 content）
            _content = msg.get("content", "")
            if _content is None:
                _content = ""
            if isinstance(_content, list):
                # 多模态消息：提取文本部分
                _text_parts = []
                for _item in _content:
                    if isinstance(_item, dict) and _item.get("type") == "text":
                        _t = _item.get("text", "")
                        if isinstance(_t, str):
                            _text_parts.append(_t)
                    elif isinstance(_item, str):
                        _text_parts.append(_item)
                _content = "\n".join(_text_parts) if _text_parts else ""
            _clean["content"] = _content
            # reasoning_content: 仅思考模式模型（DeepSeek/Qwen）需要传回
            if _supports_thinking and "reasoning_content" in msg:
                _clean["reasoning_content"] = msg["reasoning_content"]
            # tool_calls: 只保留标准字段
            if "tool_calls" in msg:
                _clean_tcs = []
                for tc in msg["tool_calls"]:
                    _tc = {"type": tc.get("type", "function")}
                    if "id" in tc:
                        _tc["id"] = tc["id"]
                    if "function" in tc:
                        _fn = {}
                        if "name" in tc["function"]:
                            _fn["name"] = tc["function"]["name"]
                        if "arguments" in tc["function"]:
                            _fn["arguments"] = tc["function"]["arguments"]
                        _tc["function"] = _fn
                    _clean_tcs.append(_tc)
                _clean["tool_calls"] = _clean_tcs
            # tool 消息
            if msg.get("role") == "tool":
                if "tool_call_id" in msg:
                    _clean["tool_call_id"] = msg["tool_call_id"]
            # name 字段（可选）
            if "name" in msg:
                _clean["name"] = msg["name"]
            _clean_msgs.append(_clean)
        # 替换 final_messages（通过 api_params 的引用）
        final_messages.clear()
        final_messages.extend(_clean_msgs)

        # 修复 tool_calls 完整性：确保每个 assistant 的 tool_calls 后面
        # 都有对应的 tool 响应消息。如果缺失，移除 tool_calls 避免API 400错误
        _fixed_msgs = []
        _pending_tc_ids = set()
        for _idx, _msg in enumerate(final_messages):
            if _msg.get("role") == "assistant" and _msg.get("tool_calls"):
                _tc_ids = {tc.get("id") for tc in _msg["tool_calls"] if tc.get("id")}
                # 检查后续消息中是否有对应的 tool 响应
                _has_all_responses = True
                for _tc_id in _tc_ids:
                    _found = False
                    for _j in range(_idx + 1, len(final_messages)):
                        if final_messages[_j].get("role") == "tool" and final_messages[_j].get("tool_call_id") == _tc_id:
                            _found = True
                            break
                    if not _found:
                        _has_all_responses = False
                        break
                if not _has_all_responses:
                    # 移除 tool_calls，保留 content
                    _msg_copy = {k: v for k, v in _msg.items() if k != "tool_calls"}
                    if not _msg_copy.get("content"):
                        _msg_copy["content"] = ""
                    logger.warning(f"[TOOL] 移除不完整的 tool_calls（缺少tool响应），assistant消息保留为纯文本")
                    _fixed_msgs.append(_msg_copy)
                    continue
            # 移除孤立的 tool 响应消息（没有对应 assistant tool_calls 的）
            if _msg.get("role") == "tool":
                _tc_id = _msg.get("tool_call_id")
                _has_matching_call = False
                for _j in range(len(_fixed_msgs) - 1, -1, -1):
                    _prev = _fixed_msgs[_j]
                    if _prev.get("role") == "assistant" and _prev.get("tool_calls"):
                        if _tc_id in {tc.get("id") for tc in _prev["tool_calls"] if tc.get("id")}:
                            _has_matching_call = True
                            break
                    # 不因 user 消息而停止向前搜索（user 消息可能被插入在 tool 响应之间）
                if not _has_matching_call:
                    logger.warning(f"[TOOL] 移除孤立的 tool 响应消息 (tool_call_id={_tc_id})")
                    continue
            _fixed_msgs.append(_msg)
        final_messages.clear()
        final_messages.extend(_fixed_msgs)

        # SSE keepalive：每轮 API 调用前发送，防止客户端在模型响应等待期间 idle timeout
        if _round > 0:
            yield ": keepalive\n\n"

        # 第一轮用流式调用，逐 token 透传（创建副本避免修改原始参数）
        round_params = {**api_params, "stream": True}
        stream = None
        for _api_attempt in range(API_MAX_RETRIES):
            try:
                stream = client.chat.completions.create(**round_params)
                break  # 成功
            except Exception as e:
                if _is_retryable_error(e) and _api_attempt < API_MAX_RETRIES - 1:
                    logger.warning(f"[STREAM-RETRY] 工具轮 第{_api_attempt+1}次 API 调用失败: {e}，{API_RETRY_DELAY}秒后重试...")
                    time.sleep(API_RETRY_DELAY)
                    continue
                else:
                    logger.error(f"[STREAM] 生成错误: {e}")
                    yield _sse_error(f"生成错误: {e}")
                    yield "data: [DONE]\n\n"
                    try:
                        reset_tool_session(_tool_sid)
                    except Exception:
                        pass
                    return

        # 收集流式响应（含流式读取重试）
        collected_content = ""
        collected_reasoning = ""  # DeepSeek/Qwen 思考模式
        collected_tool_calls = {}  # {index: {id, type, function: {name, arguments}}}
        finish_reason = None

        try:
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 收集文本内容（不立即透传，等确认无 tool_calls 后再透传）
                if delta.content:
                    collected_content += delta.content

                # 收集 reasoning_content 并实时透传给客户端（思考过程不涉及工具调用，安全转发）
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    collected_reasoning += delta.reasoning_content
                    yield _sse_chunk({"reasoning_content": delta.reasoning_content})

                # 收集 tool_calls（流式增量）
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in collected_tool_calls:
                            collected_tool_calls[idx] = {
                                "id": tc_delta.id or "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        if tc_delta.id:
                            collected_tool_calls[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                collected_tool_calls[idx]["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                collected_tool_calls[idx]["function"]["arguments"] += tc_delta.function.arguments

                # 收集 finish_reason
                cfr = getattr(chunk.choices[0], 'finish_reason', None)
                if cfr:
                    finish_reason = cfr

                # 收集 usage
                if hasattr(chunk, 'usage') and chunk.usage:
                    _usage_info = {
                        "prompt_tokens": chunk.usage.prompt_tokens or 0,
                        "completion_tokens": chunk.usage.completion_tokens or 0,
                        "total_tokens": chunk.usage.total_tokens or 0,
                        "prompt_cache_hit_tokens": getattr(chunk.usage, 'prompt_cache_hit_tokens', 0) or 0,
                        "prompt_cache_miss_tokens": getattr(chunk.usage, 'prompt_cache_miss_tokens', 0) or 0
                    }
                    _cache_accum["prompt_tokens"] += _usage_info["prompt_tokens"]
                    _cache_accum["completion_tokens"] += _usage_info["completion_tokens"]
                    _cache_accum["total_tokens"] += _usage_info["total_tokens"]
                    _cache_accum["prompt_cache_hit_tokens"] += _usage_info["prompt_cache_hit_tokens"]
                    _cache_accum["prompt_cache_miss_tokens"] += _usage_info["prompt_cache_miss_tokens"]
        except Exception as e:
            logger.warning(f"[STREAM-RETRY] 工具轮流式读取中断: {e}")
            # 流式读取中断时，如果已有 tool_calls 但不完整，丢弃本轮结果
            if _is_retryable_error(e) and not collected_tool_calls:
                # 没有 tool_calls 时可以安全重试
                logger.warning(f"[STREAM-RETRY] 无 tool_calls，重试 API 调用...")
                time.sleep(API_RETRY_DELAY)
                try:
                    stream = client.chat.completions.create(**round_params)
                    for chunk in stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if delta.content:
                            collected_content += delta.content
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            collected_reasoning += delta.reasoning_content
                            yield _sse_chunk({"reasoning_content": delta.reasoning_content})
                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            for tc_delta in delta.tool_calls:
                                idx = tc_delta.index
                                if idx not in collected_tool_calls:
                                    collected_tool_calls[idx] = {
                                        "id": tc_delta.id or "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                if tc_delta.id:
                                    collected_tool_calls[idx]["id"] = tc_delta.id
                                if tc_delta.function:
                                    if tc_delta.function.name:
                                        collected_tool_calls[idx]["function"]["name"] += tc_delta.function.name
                                    if tc_delta.function.arguments:
                                        collected_tool_calls[idx]["function"]["arguments"] += tc_delta.function.arguments
                        cfr = getattr(chunk.choices[0], 'finish_reason', None)
                        if cfr:
                            finish_reason = cfr
                        if hasattr(chunk, 'usage') and chunk.usage:
                            _usage_info = {
                                "prompt_tokens": chunk.usage.prompt_tokens or 0,
                                "completion_tokens": chunk.usage.completion_tokens or 0,
                                "total_tokens": chunk.usage.total_tokens or 0,
                                "prompt_cache_hit_tokens": getattr(chunk.usage, 'prompt_cache_hit_tokens', 0) or 0,
                                "prompt_cache_miss_tokens": getattr(chunk.usage, 'prompt_cache_miss_tokens', 0) or 0
                            }
                            _cache_accum["prompt_tokens"] += _usage_info["prompt_tokens"]
                            _cache_accum["completion_tokens"] += _usage_info["completion_tokens"]
                            _cache_accum["total_tokens"] += _usage_info["total_tokens"]
                            _cache_accum["prompt_cache_hit_tokens"] += _usage_info["prompt_cache_hit_tokens"]
                            _cache_accum["prompt_cache_miss_tokens"] += _usage_info["prompt_cache_miss_tokens"]
                except Exception as e2:
                    logger.error(f"[STREAM-RETRY] 重试也失败: {e2}")
            else:
                logger.error(f"[STREAM] 工具轮流式读取失败（不可重试）: {e}")

        # 判断是否有 tool_calls（包括 API 结构化的和 DSML 文本格式的）
        if not collected_tool_calls:
            # 检查 content 中是否包含 DSML 格式的工具调用（DeepSeek 有时会输出这种格式）
            dsml_calls = parse_dsml_tool_calls(collected_content)
            if dsml_calls:
                logger.info(f"[TOOL-DSML] 从 content 中解析到 {len(dsml_calls)} 个 DSML 工具调用")
                for i, tc in enumerate(dsml_calls):
                    collected_tool_calls[i] = tc
                # 从 content 中彻底移除所有 DSML 相关内容
                before = len(collected_content)
                # 先移除完整的 DSML 块
                dsml_block_pattern = re.compile(
                    r'<｜｜DSML｜｜tool_calls>.*?</｜｜DSML｜｜tool_calls>',
                    re.DOTALL
                )
                collected_content = dsml_block_pattern.sub('', collected_content)
                # 再移除任何残留的 DSML 标签（不完整的也移除）
                collected_content = re.sub(r'<｜｜DSML｜｜[^>]*>', '', collected_content)
                collected_content = re.sub(r'</｜｜DSML｜｜[^>]*>', '', collected_content)
                # 移除可能残留的 DSML 片段（如跨行的半个标签）
                collected_content = re.sub(r'<｜｜.*?｜｜>', '', collected_content)
                collected_content = collected_content.strip()
                logger.info(f"[TOOL-DSML] content 从 {before} 字符减至 {len(collected_content)} 字符")
            elif '<｜｜DSML｜｜' in collected_content or '<｜｜' in collected_content:
                logger.warning(f"[TOOL-DSML] content 中包含 DSML 标签但解析失败，content={collected_content[:200]}")
                before = len(collected_content)
                # 彻底移除所有 DSML 相关内容
                collected_content = re.sub(r'<｜｜DSML｜｜[^>]*>', '', collected_content)
                collected_content = re.sub(r'</｜｜DSML｜｜[^>]*>', '', collected_content)
                collected_content = re.sub(r'<｜｜.*?｜｜>', '', collected_content)
                collected_content = collected_content.strip()
                logger.info(f"[TOOL-DSML] 强制清理后 content 从 {before} 字符减至 {len(collected_content)} 字符")

        if not collected_tool_calls:
            # 纯文本回复，现在一次性透传所有内容
            if collected_content:
                yield _sse_chunk({"content": collected_content})
            yield _sse_chunk({}, finish_reason or "stop", usage=_cache_accum if _cache_accum["prompt_tokens"] > 0 else None)
            yield "data: [DONE]\n\n"
            try:
                reset_tool_session(_tool_sid)
            except Exception:
                pass
            return

        # 有 tool_calls，但如果有文本也透传给客户端（避免丢失中间回答）
        if collected_content:
            yield _sse_chunk({"content": collected_content})
            logger.info(f"[TOOL] 第{_round+1}轮: 检测到 {len(collected_tool_calls)} 个工具调用，已透传 {len(collected_content)} 字符文本")
        else:
            logger.info(f"[TOOL] 第{_round+1}轮: 检测到 {len(collected_tool_calls)} 个工具调用")

        # 构建 tool_calls 列表
        tool_calls_list = [collected_tool_calls[i] for i in sorted(collected_tool_calls.keys())]

        # 确保每个 tool_call 都有非空 id（API要求 tool_call_id 必须匹配）
        for i, tc in enumerate(tool_calls_list):
            if not tc.get("id"):
                tc["id"] = f"call_{uuid.uuid4().hex[:12]}"
                logger.warning(f"[TOOL] 为 tool_call[{i}] 补充缺失的id: {tc['id']}")

        # 中间轮次不向客户端发送 tool_calls（防止 Open WebUI 停止渲染后续内容）
        # 只在 Open WebUI 作为真正的 tool 循环代理时才发送 tool_calls + finish_reason
        # 我们的服务端内部自行处理 tool 循环，客户端只需最终文本

        # 构建 assistant 消息（含 tool_calls + reasoning_content）
        assistant_msg = {
            "role": "assistant",
            "content": collected_content or "",
            "tool_calls": tool_calls_list
        }
        # 思考模式模型（DeepSeek/Qwen）：必须传回 reasoning_content
        if _supports_thinking:
            if collected_reasoning:
                assistant_msg["reasoning_content"] = collected_reasoning
            elif _compact_done:
                assistant_msg["reasoning_content"] = ""
        final_messages.append(assistant_msg)

        # 防止模型疯狂调用工具：每轮最多执行 5 个 tool_calls
        max_calls_per_round = 5
        # token 节省整改 B：每轮注入「推导状态」（已确认结论 + 待办），引导模型续推而非重搜
        # 先移除上一轮注入的状态消息（用标记匹配，防重复累积）
        final_messages[:] = [m for m in final_messages if "__DERIV_STATE__" not in str(m.get("content") or "")]
        _deriv_state = _extract_derivation_state(final_messages)
        if _deriv_state:
            _state_msg = {
                "role": "system",
                "content": _deriv_state + "\n__DERIV_STATE__",
            }
            # 注入到 system 之后（final_messages[0] 是主 system），避免污染原始 system
            final_messages.insert(1, _state_msg)
            logger.info(f"[DERIV-STATE] 注入推导状态: {_deriv_state[:80]}... (len={len(_deriv_state)})")
        # 统计同一工具的累计调用次数，超过阈值后只返回摘要
        _tool_call_counts = {}
        for tc_info in tool_calls_list:
            fn = tc_info["function"]["name"]
            _tool_call_counts[fn] = _tool_call_counts.get(fn, 0) + 1
        # 累加到全局计数器
        for fn, cnt in _tool_call_counts.items():
            _total_tool_calls[fn] = _total_tool_calls.get(fn, 0) + cnt
        # 动态限制 view_article：大文章（已读>100K字符）不限制，小文章限制 15 次
        _view_count = _total_tool_calls.get("view_article", 0)
        if _total_view_chars > 100000:
            _view_limit = 999  # 大文章放开
        else:
            _view_limit = 15
        if _view_count > _view_limit:
            logger.warning(f"[TOOL] view_article 全局累计 {_view_count} 次（已读 {_total_view_chars} 字符，限制 {_view_limit} 次），本轮跳过所有 view_article")
            new_tool_calls_list = []
            for tc_info in tool_calls_list:
                if tc_info["function"]["name"] == "view_article":
                    final_messages.append({
                        "role": "tool",
                        "tool_call_id": tc_info["id"],
                        "content": "提示：你已浏览了足够的文章，请直接基于已有信息回答用户问题，不要再继续查看文章。"
                    })
                else:
                    new_tool_calls_list.append(tc_info)
            tool_calls_list = new_tool_calls_list

        # 限制每轮执行数量
        if len(tool_calls_list) > max_calls_per_round:
            skipped = tool_calls_list[max_calls_per_round:]
            tool_calls_list = tool_calls_list[:max_calls_per_round]
            for tc_info in skipped:
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tc_info["id"],
                    "content": "提示：本轮工具调用数量已达上限，请精简你的请求，直接回答用户问题。"
                })
            logger.warning(f"[TOOL] 每轮限制 {max_calls_per_round} 个调用，跳过 {len(skipped)} 个")

        yield ": keepalive\n\n"  # SSE keepalive：工具执行期间防止客户端 idle timeout

        _inject_budget_warning = False  # Token 预算保护标志（延迟到所有 tool 响应后插入）
        for tc_info in tool_calls_list:
            func_name = tc_info["function"]["name"]
            try:
                func_args = json.loads(tc_info["function"]["arguments"]) if tc_info["function"]["arguments"] else {}
            except json.JSONDecodeError:
                func_args = {}

            call_sig = f"{func_name}:{json.dumps(func_args, sort_keys=True)}"
            if call_sig in seen_calls:
                logger.warning(f"[TOOL] 重复调用已跳过: {func_name}")
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tc_info["id"],
                    "content": f"警告：此工具调用与之前重复，已跳过。请直接使用之前的结果回答，不要再调用工具。"
                })
                continue
            # 先加入集合（防止并发重复），失败后移除允许重试
            seen_calls.add(call_sig)

            logger.info(f"[TOOL] 执行: {func_name}({list(func_args.keys())})")
            # 护法：记录文件读取，检测重复读取
            _guardian_advice = ""
            if func_name in ("view_article", "file_read"):
                _fname = func_args.get("filename", "") or func_args.get("file", "")
                if _fname and _read_tracker.record_read(_fname):
                    _guardian_advice = _read_tracker.get_repeat_advice(_fname)
                    logger.warning(
                        f"[GUARDIAN] 重复读取触发: {_fname} "
                        f"(已读 {_read_tracker.read_count[_fname]} 次)，"
                        f"将注入护法建议"
                    )
            # 工具执行失败重试（最多2次）
            result = None
            for _retry in range(2):
                try:
                    result = execute_tool_call(func_name, func_args, vector_kb=vector_kb, session_id=_tool_sid)
                    if result and not result.startswith("工具执行错误"):
                        break
                    logger.warning(f"[TOOL] 第{_retry+1}次执行失败: {result[:100]}")
                except Exception as e:
                    logger.warning(f"[TOOL] 第{_retry+1}次执行异常: {e}")
                    result = None
            if not result:
                result = f"工具 {func_name} 执行失败，请尝试其他方式获取信息。"
            # 仅在工具执行异常（非"文件不存在"类错误）时允许重试
            # "文件不存在"不重试：文件不会凭空出现，重试只会浪费轮次
            if result and result.startswith("错误") and "不存在" not in result:
                seen_calls.discard(call_sig)
                logger.info(f"[TOOL] 工具执行异常，已从去重集合移除，允许重试: {func_name}")
            # Token 节省：工具结果累计估算
            _total_tool_input_tokens += int(len(result) * 1.5)
            # 追踪 view_article 读取的原始文章大小（从返回文本中提取）
            if func_name == "view_article" and "(共" in result:
                import re as _re_vc
                m = _re_vc.search(r'共(\d+)字符', result)
                if m:
                    _total_view_chars += int(m.group(1))
            # 单个工具结果超长修剪（token 节省整改 2026-08-26 升级：dsh pruner 风格）
            # 保头部 3000 + 尾部 2000 + 中间标记 —— 尾部常含关键结论（数值/结论行）
            _MAX_TOOL_RESULT_CHARS = 8192
            _TOOL_HEAD_CHARS = 3000
            _TOOL_TAIL_CHARS = 2000
            _TOOL_PRUNE_MARKER = "\n\n[... 工具结果中部已修剪，原始长度 {orig} 字符。如需中间内容请用 offset/limit 或 section 精确读取 ...]\n\n"
            if len(result) > _MAX_TOOL_RESULT_CHARS:
                _orig_len = len(result)
                result = (result[:_TOOL_HEAD_CHARS]
                          + _TOOL_PRUNE_MARKER.format(orig=_orig_len)
                          + result[-_TOOL_TAIL_CHARS:])
                logger.info(f"[TOOL] 工具结果超长，头/尾修剪至 {_TOOL_HEAD_CHARS}+{_TOOL_TAIL_CHARS} (原始 {_orig_len} 字符)")
            logger.info(f"[TOOL] 结果: {result[:150].replace(chr(10), chr(92)+chr(110))}... (累计工具结果约 {_total_tool_input_tokens} token, view_article累计 {_total_view_chars} 字符)")
            # 护法：如果有重复读取建议，追加到工具结果中
            if _guardian_advice:
                result = _guardian_advice + "\n\n--- 文章内容 ---\n\n" + result
                logger.info(f"[GUARDIAN] 已将护法建议追加到工具结果 ({len(_guardian_advice)} 字符)")
            final_messages.append({
                "role": "tool",
                "tool_call_id": tc_info["id"],
                "content": result
            })

            # Token 预算保护：如果工具结果累计超过 35000 token，
            # 标记需要注入停止提示（延迟到所有 tool 响应之后插入，避免破坏 tool_calls 连续性）
            if _total_tool_input_tokens > 35000:
                _inject_budget_warning = True
                logger.warning(f"[TOOL] Token 预算 {_total_tool_input_tokens} 已超 35000，标记注入停止提示")

    # 延迟注入 Token 预算保护消息（确保不破坏 tool_calls → tool 响应的连续性）
    if _inject_budget_warning:
        final_messages.append({
            "role": "user",
            "content": "【系统提示】工具调用已消耗大量上下文，请基于已有信息直接回答用户，不要再调用工具。"
        })
        logger.info(f"[TOOL] 延迟注入 Token 预算保护消息（所有 tool 响应之后）")

    # token 节省整改（硬约束）：工具结果累计超过硬上限时，不等 25 轮，直接强制文本收尾
    # 之前的 35000 只是"建议提示"，模型可无视（实测 23:14 会话跑到 139K token 仍在读文章）
    _TOOL_TOKEN_HARD_CAP = 60000
    if _total_tool_input_tokens > _TOOL_TOKEN_HARD_CAP:
        logger.warning(f"[TOOL] 工具结果累计 {_total_tool_input_tokens} token 超过硬上限 {_TOOL_TOKEN_HARD_CAP}，强制文本收尾")
        final_messages.append({
            "role": "user",
            "content": "【系统指令】工具调用已消耗过多上下文（远超预算）。请立即停止调用任何工具，"
                       "基于已有信息直接用纯文本给出你的推导/结论。不要输出任何工具调用格式（不要输出 <｜｜DSML｜｜ 等标签）。"
        })
        # 最终回复前也清洗 reasoning_content
        for msg in final_messages:
            if "reasoning_content" in msg:
                del msg["reasoning_content"]
        final_api_params = {k: v for k, v in api_params.items() if k != "tools"}
        try:
            yield from _stream_text(final_api_params)
        except Exception as e:
            logger.error(f"[STREAM] 最终流式生成错误: {e}")
            yield _sse_error(f"生成错误: {e}")
            yield "data: [DONE]\n\n"
        return

    # 超过轮数限制，强制要求模型直接回答 -- 真正流式
    logger.warning(f"[TOOL] 超过 {max_tool_rounds} 轮，强制生成文本回复")
    # 追加强制文本回复指令（防止模型继续输出 DSML 工具调用格式）
    final_messages.append({
        "role": "user",
        "content": "【系统指令】工具调用轮数已达上限。请直接用纯文本回答用户的问题，不要使用任何工具调用格式（不要输出 <｜｜DSML｜｜ 等标签）。"
    })
    # 最终回复前也清洗 reasoning_content
    for msg in final_messages:
        if "reasoning_content" in msg:
            del msg["reasoning_content"]
    final_api_params = {k: v for k, v in api_params.items() if k != "tools"}
    try:
        yield from _stream_text(final_api_params)
    except Exception as e:
        logger.error(f"[STREAM] 最终流式生成错误: {e}")
        yield _sse_error(f"生成错误: {e}")
        yield "data: [DONE]\n\n"
