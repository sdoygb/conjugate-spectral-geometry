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
from tools import execute_tool_call

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
    base_url, api_key = get_provider_for_model(request_model)
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    max_tool_rounds = 25
    seen_calls = set()  # 防止重复调用
    _total_tool_calls = {}  # 全局累计工具调用次数（跨轮次）
    _total_tool_input_tokens = 0  # 全局累计工具结果 token 数（估算）
    _total_view_chars = 0  # 全局累计 view_article 读取的原始文章字符数
    _resp_id = f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
    _created = int(time.time())
    _model = data.get('model', GAI_MODEL)
    _usage_info = {}

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
                            "total_tokens": chunk.usage.total_tokens or 0
                        }
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
                yield _sse_chunk({}, fr, usage=_usage_info if _usage_info else None)
                yield "data: [DONE]\n\n"
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
        # 每轮调用前彻底清洗消息（DeepSeek 兼容）
        # 策略：JSON 序列化/反序列化，只保留 OpenAI 标准字段
        _clean_msgs = []
        for msg in final_messages:
            _clean = {}
            _clean["role"] = msg.get("role", "user")
            # content: 确保不为 null
            _content = msg.get("content", "")
            if _content is None:
                _content = ""
            _clean["content"] = _content
            # reasoning_content: DeepSeek 思考模式必须传回
            if "reasoning_content" in msg:
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
                    return

        # 收集流式响应（含流式读取重试）
        collected_content = ""
        collected_reasoning = ""  # DeepSeek 思考模式
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

                # 收集 reasoning_content（DeepSeek 思考模式）
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    collected_reasoning += delta.reasoning_content

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
                        "total_tokens": chunk.usage.total_tokens or 0
                    }
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
                                "total_tokens": chunk.usage.total_tokens or 0
                            }
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
            yield _sse_chunk({}, finish_reason or "stop", usage=_usage_info if _usage_info else None)
            yield "data: [DONE]\n\n"
            return

        # 有 tool_calls，不透传文本（工具调用过程对用户透明）
        logger.info(f"[TOOL] 第{_round+1}轮: 检测到 {len(collected_tool_calls)} 个工具调用，文本不透传")

        # 构建 tool_calls 列表
        tool_calls_list = [collected_tool_calls[i] for i in sorted(collected_tool_calls.keys())]

        # 中间轮次不向客户端发送 tool_calls（防止 Open WebUI 停止渲染后续内容）
        # 只在 Open WebUI 作为真正的 tool 循环代理时才发送 tool_calls + finish_reason
        # 我们的服务端内部自行处理 tool 循环，客户端只需最终文本

        # 构建 assistant 消息（含 tool_calls + reasoning_content）
        assistant_msg = {
            "role": "assistant",
            "content": collected_content or "",
            "tool_calls": tool_calls_list
        }
        # DeepSeek 思考模式：必须传回 reasoning_content
        if collected_reasoning:
            assistant_msg["reasoning_content"] = collected_reasoning
        final_messages.append(assistant_msg)

        # 防止模型疯狂调用工具：每轮最多执行 5 个 tool_calls
        max_calls_per_round = 5
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
            # 工具执行失败重试（最多2次）
            result = None
            for _retry in range(2):
                try:
                    result = execute_tool_call(func_name, func_args, vector_kb=vector_kb)
                    if result and not result.startswith("工具执行错误"):
                        break
                    logger.warning(f"[TOOL] 第{_retry+1}次执行失败: {result[:100]}")
                except Exception as e:
                    logger.warning(f"[TOOL] 第{_retry+1}次执行异常: {e}")
                    result = None
            if not result:
                result = f"工具 {func_name} 执行失败，请尝试其他方式获取信息。"
            # 如果结果包含"不存在"或"错误"或"失败"，允许 AI 用相同参数重试
            if result and ("不存在" in result or result.startswith("错误") or "执行失败" in result):
                seen_calls.discard(call_sig)
                logger.info(f"[TOOL] 工具返回错误，已从去重集合移除，允许重试: {func_name}")
            # Token 节省：工具结果累计估算
            _total_tool_input_tokens += int(len(result) * 1.5)
            # 追踪 view_article 读取的原始文章大小（从返回文本中提取）
            if func_name == "view_article" and "(共" in result:
                import re as _re_vc
                m = _re_vc.search(r'共(\d+)字符', result)
                if m:
                    _total_view_chars += int(m.group(1))
            logger.info(f"[TOOL] 结果: {result[:150]}... (累计工具结果约 {_total_tool_input_tokens} token, view_article累计 {_total_view_chars} 字符)")
            final_messages.append({
                "role": "tool",
                "tool_call_id": tc_info["id"],
                "content": result
            })

            # Token 预算保护：如果工具结果累计超过 80000 token，
            # 在下一个 tool 消息中注入提示，要求模型尽快回答
            if _total_tool_input_tokens > 80000 and _total_tool_calls.get(func_name, 0) <= 1:
                final_messages.append({
                    "role": "user",
                    "content": "【系统提示】工具调用已消耗大量上下文，请基于已有信息直接回答用户，不要再调用工具。"
                })
                logger.warning(f"[TOOL] Token 预算 {_total_tool_input_tokens} 已超 80000，注入停止提示")

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
