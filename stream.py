"""
stream.py — 流式生成模块
从 geometry_ai_server_v5_12.py 提取
包含：stream_generate 函数
"""

import hashlib
import json
import time
from typing import List, Dict, Any

import openai

from config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, logger
from tools import execute_tool_call


def stream_generate(data: Dict[str, Any], eta_before: float, final_messages: List[Dict],
                    api_params: Dict[str, Any]) -> Any:
    client = openai.OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
    max_tool_rounds = 15
    seen_calls = set()  # 防止重复调用
    _resp_id = f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
    _created = int(time.time())
    _model = data.get('model', KIMI_MODEL)
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
                "logprobs": None,
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
        """真正流式调用 AI模型，逐 token 透传给客户端"""
        params["stream"] = True
        stream = client.chat.completions.create(**params)
        text_buf = ""
        fr = "stop"
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    text_buf += delta.content
                    yield _sse_chunk({"content": delta.content})
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
        yield _sse_chunk({}, fr, usage=_usage_info if _usage_info else None)
        yield "data: [DONE]\n\n"

    # 第一个 chunk：发送 role
    yield _sse_chunk({"role": "assistant", "content": ""})

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
        try:
            stream = client.chat.completions.create(**round_params)
        except Exception as e:
            logger.error(f"[STREAM] 生成错误: {e}")
            yield _sse_error(f"生成错误: {e}")
            yield "data: [DONE]\n\n"
            return

        # 收集流式响应
        collected_content = ""
        collected_reasoning = ""  # DeepSeek 思考模式
        collected_tool_calls = {}  # {index: {id, type, function: {name, arguments}}}
        finish_reason = None

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

        # 判断是否有 tool_calls
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
            seen_calls.add(call_sig)

            logger.info(f"[TOOL] 执行: {func_name}({list(func_args.keys())})")
            # 工具执行失败重试（最多2次）
            result = None
            for _retry in range(2):
                try:
                    result = execute_tool_call(func_name, func_args)
                    if result and not result.startswith("工具执行错误"):
                        break
                    logger.warning(f"[TOOL] 第{_retry+1}次执行失败: {result[:100]}")
                except Exception as e:
                    logger.warning(f"[TOOL] 第{_retry+1}次执行异常: {e}")
                    result = None
            if not result:
                result = f"工具 {func_name} 执行失败，请尝试其他方式获取信息。"
            logger.info(f"[TOOL] 结果: {result[:150]}...")
            final_messages.append({
                "role": "tool",
                "tool_call_id": tc_info["id"],
                "content": result
            })

    # 超过轮数限制，强制要求模型直接回答 -- 真正流式
    logger.warning(f"[TOOL] 超过 {max_tool_rounds} 轮，强制生成文本回复")
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
