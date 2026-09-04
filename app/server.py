"""





server.py - 共扼谱几何AI调度中间层主入口
从 geometry_ai_server_v5_12.py 提取的 Flask 路由和启动代码
"""

import os

# 清除代理环境变量，防止 http_proxy 影响服务器 API 请求（DeepSeek/SiliconFlow 等）
for _pv in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(_pv, None)
os.environ['NO_PROXY'] = '*'
import re
import math
import json
import hashlib
import logging
import time
import threading
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

import openai
import httpx as _httpx
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import (logger, GAI_API_KEY, GAI_BASE_URL, GAI_MODEL, GAI_MODEL_LITE, GAI_MODEL_VISION,
                    GAI_EMBEDDING_MODEL, UPLOAD_FOLDER, OPENWEBUI_UPLOAD_DIR, OPENWEBUI_DB_PATH,
                    MAX_INJECT_CHARS, QUALITY_GATE_ENABLED, MAX_QUALITY_RETRIES,
                    _injected_files, _injected_files_lock, openai_error,
                    CHROMA_DB_DIR, CHROMADB_AVAILABLE, EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL,
                    CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_QUERY, PERSONAL_DB_PATH,
                    LEARN_COHERENCE_THRESHOLD, LEARN_MIN_LENGTH, GEOMETRY_CONSTANTS,
                    EXTRA_MODELS, get_provider_for_model, get_available_models)
from version import VERSION, BUILD_DATE
from knowledge import VectorKnowledgeBase, APIEmbeddingFunction, LocalEmbeddingFunction
from models import (personal_db, _save_personal_db, _get_personal_db_summary, LivingInfoField,
                    compute_geo_density, extract_key_propositions, find_file_by_reference,
                    extract_text_from_file, allowed_file, scan_openwebui_recent_uploads,
                    save_conversation, save_phase_marker, get_stage, get_strategy,
                    update_eta_living, check_phase_marker, _memory_conversations, _memory_phase_markers)
from prompts import TeachingSystem, build_system_prompt, check_response_quality, check_correction_applied
from tools import (ARTICLE_TOOLS, execute_tool_call, parse_and_execute_tools, OPENAPI_SPEC,
                   vector_kb as _tools_vector_kb, teaching_system as _tools_teaching,
                   living_field as _tools_living, reset_tool_session, set_session_mode,
                   init_session_mode, _CODING_KEYWORDS)
from citation_check import load_real_article_ids, verify_citations, format_bad_citations
from stream import stream_generate
from guardian import generate_opening_advice, extract_article_numbers, is_derivation_query
from admin_routes import admin_bp
from share_routes import share_bp
from gap_workbench.service import workbench_bp as _workbench_bp, WorkbenchRegistry as _WorkbenchRegistry, SessionStore as _SessionStore

app = Flask(__name__)
app.register_blueprint(admin_bp)
app.register_blueprint(share_bp)
app.register_blueprint(_workbench_bp)  # 工作台常驻服务（全内存）
CORS(app)

# 全局错误处理器：确保所有错误返回 JSON 格式
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def _handle_error(e):
    return openai_error(str(e), status=getattr(e, 'code', 500))

@app.errorhandler(Exception)
def _handle_exception(e):
    import traceback
    tb = traceback.format_exc()
    logger.error(f"[UNHANDLED] {type(e).__name__}: {e}\n{tb}")
    return openai_error(f"内部服务器错误: {str(e)[:200]}", status=500)

# 简单 rate limiting：每分钟最多 60 次请求（per IP）
_rate_limit_store = {}  # {ip: [(timestamp, count), ...]}
_RATE_LIMIT_PER_MIN = 60

# 真实文章编号集合（引用硬校验的权威真相源），启动时从 articles 目录加载
_REAL_ARTICLE_IDS = set()

# 推导工作台 · 五线并行缓存（同目标不重复跑 5 次 LLM）
_WB_SUMMARY_CACHE = {}   # {gap_id: {"summary": str, "ts": str}}
_WB_RUNNING = set()      # 正在跑的 gap_id（防止并发重跑）
_WB_LOCK = threading.Lock()

# 推导意图 / 硬推导信号词（用于判断是否触发五线并行推导）
_WB_INTENT = ['推导', '证明', '如何得出', '为什么', '怎么来', '机制', '导出',
              '验证', '来源', '求出', '算出', '论证',
              '计算', '统计', '估算', '求值', '分析', '算算', '推演']
_WB_HARD = ['定理', '公式', '计算', '谱', '特征值', '作用量', '不变量', '守恒量',
            '曲率', 'θ', 'θσ', 'λ', 'α', 'κ', 'Λ']


def _workbench_gate(clean_query: str, has_results: bool, diag: bool = True) -> bool:
    """是否触发五线并行推导：仅对真正的硬推导题启用。

    diag=True 时，把未触发的原因逐条打到日志（[WB-GATE]），用于排查
    "自动五线为何几乎不生效"。每道闸都留下明确记录。
    """
    q = (clean_query or "").strip()
    # 命中/未命中原因收集，仅当 diag=True 且未通过时输出，避免噪声日志
    def _reject(reason: str) -> bool:
        if diag:
            logger.info(f"[WB-GATE] 不触发五线：{reason} | query={q[:40]}")
        return False

    if len(q) < 20:
        return _reject(f"query 过短(<20字, len={len(q)})")
    if not any(k in q for k in _WB_INTENT):
        return _reject(f"无推导意图词(_WB_INTENT): {q[:40]}")
    if not any(k in q for k in _WB_HARD):
        return _reject(f"无硬推导信号词(_WB_HARD): {q[:40]}")
    # 排除检索定位型 / 闲聊 / 自动请求
    if any(k in q for k in ['哪篇文章', '哪些文章', '搜一搜', '哪篇', '查编号',
                            '你好', '谢谢', '再见']):
        return _reject("命中排除词(检索/闲聊)")
    if os.getenv('GAP_WORKBENCH_AUTO', '1') == '0':
        return _reject("GAP_WORKBENCH_AUTO=0 已禁用")
    if not has_results:
        return _reject("无检索结果(has_results=False)")
    return True


def _workbench_anchors(results: list) -> List[str]:
    """从检索结果里提取文章编号作为工作台锚点（去重、保序，最多 8 个）。"""
    out: List[str] = []
    seen = set()
    for r in results or []:
        fn = (r.get('metadata') or {}).get('fname', '') or (r.get('fname') or '')
        # 兼容真实命名 `10.61_标题_CN..md`（下划线是 \w，\b 不会触发，
        # 故用能匹配数字后的 '._' 分隔的显式边界）
        m = re.search(r'(?<!\d)(\d+(?:\.\d+)+)(?=[_\W]|$)', fn)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
        if len(out) >= 8:
            break
    return out


# ==================== 对话历史渐进压缩（token 节省整改 2026-08-26） ====================
# 超过阈值时，把早期历史用 LLM 压缩成「进度快照」，保留尾部原文。
# 参照 dsh-compaction-basic 的比例制设计（2026-08-26 升级）：
#   thresholdTokens = contextWindow × thresholdRatio（触发阈值）
#   retainTokens    = contextWindow × retainRatio   （保留尾部）
# 与现有 TRIM（粗暴删除）互补：TRIM 管条数上限，本机制管字符数超限且保留推导链。
# 各模型上下文窗口（token 数）；未知模型回退 default
_MODEL_CONTEXT_WINDOWS = {
    'deepseek-v4-flash': 131072,   # 128K
    'deepseek-v4-pro': 131072,
    'deepseek-chat': 131072,
    'deepseek-reasoner': 131072,
    'qwen3.7-flash': 65536,        # 64K 小窗口 → 更早压缩
    'qwen3-flash': 65536,
    'doubao-seed-2-1-pro-260628': 65536,
    'doubao-seed-2-1-turbo-260628': 65536,
    'glm-4.7-flash': 65536,
    'Qwen/Qwen2.5-7B-Instruct': 32768,   # 硅基流动免费模型 32K
    'default': 131072,
}
_HISTORY_THRESHOLD_RATIO = 0.8    # 触发阈值 = 窗口 × 80%
_HISTORY_RETAIN_RATIO = 0.16      # 保留尾部 = 窗口 × 16%
_HISTORY_CHARS_PER_TOKEN = 2.0    # token→字符估算系数（中文约 1 token≈1.5-2 字符，取 2 偏保守）
_HISTORY_SNAPSHOT_MAX_CHARS = 8000  # 快照自身长度上限（防止快照无限膨胀）
_HISTORY_SNAPSHOT_MARK = "【对话进度快照（自动压缩）】"


def _model_context_window(model: str = None) -> int:
    """按模型返回上下文窗口 token 数（未知模型回退 default）。"""
    _m = (model or GAI_MODEL or '').lower()
    for _k, _w in _MODEL_CONTEXT_WINDOWS.items():
        if _k.lower() in _m:
            return _w
    return _MODEL_CONTEXT_WINDOWS['default']


def _history_threshold_chars(model: str = None) -> int:
    """比例制触发阈值（字符）= 窗口 × 80% × 2 字符/token。"""
    return int(_model_context_window(model) * _HISTORY_THRESHOLD_RATIO * _HISTORY_CHARS_PER_TOKEN)


def _history_retain_chars(model: str = None) -> int:
    """比例制保留尾部（字符）= 窗口 × 16% × 2 字符/token。"""
    return int(_model_context_window(model) * _HISTORY_RETAIN_RATIO * _HISTORY_CHARS_PER_TOKEN)


def _history_messages_chars(msgs: List[Dict]) -> int:
    """估算消息列表总字符数（与 TRIM 一致的口径）。"""
    return sum(len(json.dumps(m, ensure_ascii=False)) for m in msgs)


def _find_snapshot_idx(msgs: List[Dict]) -> int:
    """查找已有进度快照消息的索引（渐进压缩：存在则跳过已压缩部分）。"""
    for i, m in enumerate(msgs):
        if isinstance(m.get("content"), str) and _HISTORY_SNAPSHOT_MARK in m["content"]:
            return i
    return -1


def _llm_summarize_history(messages: List[Dict], model: str = None) -> str:
    """用 LLM 把一段对话历史压缩成进度快照。失败返回空串（由调用方降级）。"""
    try:
        _sum_model = model or GAI_MODEL
        _burl, _akey = get_provider_for_model(_sum_model)
        _client = openai.OpenAI(api_key=_akey, base_url=_burl,
                                http_client=_httpx.Client(trust_env=False),
                                timeout=60.0, max_retries=1)
        _text = ""
        for m in messages:
            _c = m.get("content")
            if isinstance(_c, str):
                _text += f"[{m.get('role')}] {_c[:600]}\n"
            elif isinstance(_c, list):
                _text += f"[{m.get('role')}] (多模态)\n"
        if not _text.strip():
            return ""
        _sys = (
            "你是对话历史的压缩器。把用户提供的多轮对话（含工具调用）压缩成一份「进度快照」，"
            "供另一个 LLM 继续推导时快速恢复上下文。必须保留：\n"
            "1. 已确认的推导结论/关键数值（含 calculate_math 算出的数）\n"
            "2. 已读取过的文章文件名和大致区间\n"
            "3. 已排除的方案/死胡同\n"
            "4. 当前卡点与下一步待办\n"
            "丢弃：重复内容、失败尝试、过长引用原文。输出用中文，简洁条目式，总长控制在 3000 字以内。"
        )
        _resp = _client.chat.completions.create(
            model=_sum_model,
            messages=[{"role": "system", "content": _sys},
                      {"role": "user", "content": _text[:100000]}],  # 防超长输入
            max_tokens=4000,
        )
        _sum_text = (_resp.choices[0].message.content or "").strip()
        if not _sum_text:
            return ""
        # 强制加标记前缀，供渐进压缩的 _find_snapshot_idx 识别
        return _HISTORY_SNAPSHOT_MARK + "\n" + _sum_text
    except Exception as _e:
        logger.warning(f"[HISTORY-COMPACT] LLM 摘要失败，降级规则式: {_e}")
        return ""


def _rule_summarize_history(messages: List[Dict]) -> str:
    """规则式兜底摘要（不调模型）：提取每条消息首行关键信息。"""
    parts = []
    for m in messages:
        _c = m.get("content")
        if isinstance(_c, str) and _c.strip():
            parts.append(f"[{m.get('role')}] {_c[:200].replace(chr(10), ' ')}")
    return _HISTORY_SNAPSHOT_MARK + "\n（规则式摘要）\n" + "\n".join(parts[:30])


def compact_history_messages(messages: List[Dict], model: str = None,
                             threshold: int = None) -> List[Dict]:
    """渐进压缩对话历史（比例制，参照 dsh-compaction-basic 2026-08-26）：
    - 触发阈值 = 模型窗口 × 80%（threshold），字符超限即压缩
    - 保留尾部 = 模型窗口 × 16%（retain），从尾部逐轮回溯直到达保留预算
    - 早期消息用 LLM 压缩成进度快照（失败降级规则式）

    渐进性：已有快照时只压缩「快照之后、保留区之前」的部分；快照自身超长则重新摘要。
    返回新的消息列表（未超限时原样返回）。
    """
    # 比例制：阈值/保留随模型窗口缩放
    _model = model or GAI_MODEL
    _thr = threshold or _history_threshold_chars(_model)
    _retain_chars = _history_retain_chars(_model)
    _total = _history_messages_chars(messages)
    if _total <= _thr:
        return messages

    # 比例制保留区：保留尾部 retain 预算内的内容（从尾部累积，到预算即停）
    # 参照 dsh：retainTokens = contextWindow × retainRatio —— 尾部固定保留这么多，其余压缩
    _keep_from = 1
    _acc = 0
    for _i in range(len(messages) - 1, 0, -1):  # 从尾部往前（不含 system）
        _sz = len(json.dumps(messages[_i], ensure_ascii=False))
        _acc += _sz
        if _acc >= _retain_chars or _i <= 1:
            _keep_from = _i
            break
        _keep_from = _i

    # 要压缩的部分：保留区之前（若已有快照，则从快照之后开始）
    _snap_idx = _find_snapshot_idx(messages)
    _compress_from = (_snap_idx + 1) if _snap_idx >= 0 else 1
    if _compress_from >= _keep_from:
        # 无可压缩部分（保留区已覆盖一切）→ 仍超限则强压保留区前 6 条
        _compress_from = max(1, _keep_from - 6)

    _old_part = messages[_compress_from:_keep_from]
    if not _old_part:
        return messages

    # 1) 尝试 LLM 摘要
    _snapshot_text = _llm_summarize_history(_old_part, model=model)
    if not _snapshot_text:
        _snapshot_text = _rule_summarize_history(_old_part)
    # 2) 快照长度封顶
    if len(_snapshot_text) > _HISTORY_SNAPSHOT_MAX_CHARS:
        _snapshot_text = _snapshot_text[:_HISTORY_SNAPSHOT_MAX_CHARS] + "\n...(快照超长截断)"

    _snap_msg = {"role": "system", "content": _snapshot_text}
    _new = messages[:_compress_from] + [_snap_msg] + messages[_keep_from:]
    # ④ 阴影 token 记账：记录本次压缩省掉的估算 token（dsh shadowedTokenCount 风格）
    _shadowed_tokens = int(sum(len(json.dumps(m, ensure_ascii=False)) for m in _old_part) / _HISTORY_CHARS_PER_TOKEN)
    _new_total = _history_messages_chars(_new)
    _saved = _total - _new_total
    logger.info(
        f"[HISTORY-COMPACT] 比例制压缩(model={_model or 'default'}): "
        f"{len(messages)}条/{_total}字符 → {len(_new)}条/{_new_total}字符 "
        f"| 省 {_saved}字符 ≈ {_shadowed_tokens} token | "
        f"保留尾部 {_acc}字符(窗口×{_HISTORY_RETAIN_RATIO}) | 快照 {len(_snapshot_text)}字符"
    )
    return _new


def _format_workbench_summary(wb: dict) -> str:
    """把五线并行推导结果折叠成注入 prompt 的紧凑摘要。"""
    if not wb:
        return ""
    L = [f"\n\n【五线并行推导工作台 · {wb['id']}】",
         f"目标：{wb.get('target', '')}",
         f"五线状态：{', '.join(f'{lid}={st}' for lid, st in (wb.get('lines') or {}).items())}"]
    cross = wb.get('cross_support') or []
    if cross:
        L.append("交叉印证（≥2 条线独立收敛到同一结论，单线程往往推不出）：")
        for c in cross:
            L.append(f"- 「{c['conclusion']}」← {','.join(c['lines'])}")
    if wb.get('dead'):
        L.append(f"死胡同（排除性证据）：{','.join(wb['dead'])}")
    if wb.get('converged'):
        L.append(f"收敛结论：{wb.get('conclusion', '')}")
    L.append("请结合上方多线交叉印证结果，给出最终完整推导，并在回答末尾标注工作台编号。")
    return "\n".join(L)


def _run_auto_workbench(clean_query: str, results: list, req_model: str,
                        system_prompt: str, session_id: str,
                        vector_kb=None) -> str:
    """真正执行五线并行推导，返回注入摘要（失败/重名则返回空串）。"""
    import hashlib as _hl
    anchors = _workbench_anchors(results)
    if not anchors:
        logger.info(f"[WB] 无任何可作锚点的文章编号，跳过五线（webhook 已命中 gate 但锚点抽取为空）："
                    f"query={clean_query[:40]}")
        return ""
    gap_id = "auto_" + _hl.sha1((clean_query or "").strip().encode("utf-8")).hexdigest()[:10]
    logger.info(f"[WB] 五线推导启动 {gap_id} | 模型={req_model or GAI_MODEL} "
                f"| 锚点={anchors}({len(anchors)}个) | query={clean_query[:40]}")
    cached = _WB_SUMMARY_CACHE.get(gap_id)
    if cached:
        logger.info(f"[WB] 命中缓存，复用工作台 {gap_id}")
        return cached["summary"]
    with _WB_LOCK:
        if gap_id in _WB_RUNNING:
            logger.info(f"[WB] {gap_id} 正在后台推导中，跳过重复触发")
            return ""
        _WB_RUNNING.add(gap_id)
    _wb_model = req_model or GAI_MODEL
    try:
        _burl, _akey = get_provider_for_model(_wb_model)
    except Exception as ex:
        logger.error(f"[WB] 获取 provider 失败: {ex}")
        with _WB_LOCK:
            _WB_RUNNING.discard(gap_id)
        return ""
    _client = openai.OpenAI(api_key=_akey, base_url=_burl, http_client=_httpx.Client(trust_env=False), timeout=180.0, max_retries=1)
    from gap_workbench.llm_derive import run_llm_five_line
    try:
        wb = run_llm_five_line(
            gap_id=gap_id,
            title=clean_query[:60],
            anchors=anchors,
            target=clean_query,
            base_system_prompt=system_prompt,
            client=_client,
            model=_wb_model,
            tools=ARTICLE_TOOLS,
            # token 节省整改：session 按线隔离（wb:{gap_id}:line{N}），防止五条线 calculate_math 变量互串
            execute_tool=lambda n, a, **kw: execute_tool_call(
                n, a, vector_kb=vector_kb,
                session_id=kw.get("session_id") or f"wb:{gap_id}"),
            session_mode='derive',  # 五线推导强制推导类（shell 探索预算 5 次）
            max_tool_chain=6,
            logger=logger.info,
            embed_fn=(vector_kb.embedding_fn.embed_query
                      if getattr(vector_kb, 'embedding_fn', None) is not None else None),
            semantic_threshold=0.80,
        )
    except Exception as ex:
        logger.error(f"[WB] 五线推导异常: {ex}")
        import traceback
        logger.error(traceback.format_exc(limit=4))
        with _WB_LOCK:
            _WB_RUNNING.discard(gap_id)
        try:
            reset_tool_session(f"wb:{gap_id}")  # token 节省整改：清理五线工具会话状态
        except Exception:
            pass
        return ""
    with _WB_LOCK:
        _WB_RUNNING.discard(gap_id)
    try:
        reset_tool_session(f"wb:{gap_id}")  # token 节省整改：清理五线工具会话状态
    except Exception:
        pass
    summary = _format_workbench_summary(wb)
    if summary:
        _WB_SUMMARY_CACHE[gap_id] = {"summary": summary,
                                     "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        logger.info(f"[WB] 五线推导完成 {gap_id}：闭合 {wb.get('closed')} "
                    f"死胡同 {wb.get('dead')} 交叉 {len(wb.get('cross_support') or [])} 条")
    return summary


# ================= 子AI 自动圆满判定（主库 LLM 退役后的入库判据执行者） =================
_JUDGE_PROMPT = (
    "你是共扼谱几何子AI的「圆满判定」执行者。主库的 LLM 已退役（2026-08-05），"
    "入库判据移交给你。请对下方候选定理给出入库判定。\n\n"
    "圆满判据：\n"
    "- A0（局部代数命题）：推导链【逐步骤自洽】+【依赖全部闭合】→ promote（圆满）\n"
    "- A1（整体拓扑命题）：Berry 相位 2π 闭环（closure_error≈0）+ 依赖闭合 → promote\n"
    "- 存在缺失依赖 → dependency_gap（reason 里列出缺失定理编号）\n"
    "- 推导链存在实质错误 / 不自洽 / 数值不成立 → reject\n"
    "- 材料不足或你不确定 → keep_pending（该条暂不判定，留待人工）\n\n"
    "纪律（必须遵守）：\n"
    "- 一切数值、相位、闭式误差用 calculate_math 精确计算，严禁心算。\n"
    "- 用 view_article / vector_search / list_articles 核对依赖定理是否真实存在、是否闭合，禁止编造编号。\n"
    "- 只依据材料与主库真实文章，不得臆造。\n\n"
    "最终另起一行，仅输出一行合法 JSON，格式：\n"
    '{"verdict":"promote|reject|dependency_gap|keep_pending","level":"初圆满|中圆满|上圆满|","reason":"一句话判定理由"}'
)


def _parse_judge_json(text: str) -> dict:
    import re as _re
    d: dict = {"verdict": "keep_pending", "level": "", "reason": ""}
    _vm = _re.search(r'"verdict"\s*:\s*"([^"]+)"', text)
    if _vm:
        d["verdict"] = _vm.group(1)
    _lm = _re.search(r'"level"\s*:\s*"([^"]*)"', text)
    if _lm:
        d["level"] = _lm.group(1)
    _rm = _re.search(r'"reason"\s*:\s*"?([^"}\n]+)"?', text)
    if _rm:
        d["reason"] = _rm.group(1).strip()
    return d


def _run_child_judgement_llm(material: str) -> dict:
    """子AI对单条候选公式做出圆满语义判定（带工具核对依赖/精确计算）。"""
    if not material or not material.strip():
        return {"verdict": "keep_pending", "reason": "材料为空"}
    if os.getenv('CHILD_JUDGE_DRY_LLM') == '1':
        return {"verdict": "keep_pending", "reason": "dry-run 跳过 LLM"}
    try:
        _burl, _akey = get_provider_for_model(GAI_MODEL)
        _client = openai.OpenAI(api_key=_akey, base_url=_burl, http_client=_httpx.Client(trust_env=False), timeout=180.0, max_retries=1)
    except Exception as ex:
        logger.error(f"[CHILD-JUDGE] 获取 provider 失败: {ex}")
        return {"verdict": "keep_pending", "reason": "provider 不可用"}
    messages = [
        {"role": "system", "content": _JUDGE_PROMPT},
        {"role": "user", "content": "候选定理完整判定材料：\n\n" + material},
    ]
    api_params: dict = {"model": GAI_MODEL, "messages": messages, "tools": ARTICLE_TOOLS}
    try:
        for _r in range(1, 8):
            resp = _client.chat.completions.create(**api_params)
            content = resp.choices[0].message.content or ""
            tcs = getattr(resp.choices[0].message, "tool_calls", None)
            if (not content.strip()) and tcs:
                asst_m = {"role": "assistant", "content": None, "tool_calls": []}
                for tc in tcs:
                    asst_m["tool_calls"].append({"id": tc.id, "type": "function",
                                                 "function": {"name": tc.function.name,
                                                              "arguments": tc.function.arguments}})
                messages.append(asst_m)
                for tc in tcs:
                    try:
                        _a = json.loads(tc.function.arguments or "{}")
                    except Exception:
                        _a = {}
                    try:
                        _r_ = execute_tool_call(tc.function.name, _a, vector_kb=vector_kb,
                                                session_id="child_judge")
                    except Exception as _e:
                        _r_ = f"工具执行异常: {_e}"
                    messages.append({"role": "tool", "tool_call_id": tc.id,
                                     "content": str(_r_)[:3000]})
                api_params["messages"] = messages
                logger.info(f"[CHILD-JUDGE] 判定工具链 #{_r}: {len(tcs)} 个调用")
                continue
            return _parse_judge_json(content)
        return {"verdict": "keep_pending", "reason": "判定未产出"}
    except Exception as ex:
        logger.error(f"[CHILD-JUDGE] LLM 判定失败: {ex}")
        return {"verdict": "keep_pending", "reason": f"异常: {ex}"}

def _refresh_real_article_ids():
    """刷新真实文章编号集合（引用硬校验真相源）。"""
    global _REAL_ARTICLE_IDS
    try:
        _REAL_ARTICLE_IDS = load_real_article_ids(UPLOAD_FOLDER)
        logger.info(f"[CITE-GATE] 真实文章编号集合已加载: {len(_REAL_ARTICLE_IDS)} 篇")
    except Exception as e:
        logger.error(f"[CITE-GATE] 加载真实文章编号失败: {e}")
    return _REAL_ARTICLE_IDS

@app.before_request
def _rate_limit():
    """简单的 IP 级别频率限制"""
    # 跳过健康检查和静态请求
    if request.path in ('/health', '/favicon.ico'):
        return None
    ip = request.remote_addr or 'unknown'
    now = time.time()
    minute_ago = now - 60
    # 清理过期记录
    if ip in _rate_limit_store:
        _rate_limit_store[ip] = [(t, c) for t, c in _rate_limit_store[ip] if t > minute_ago]
    else:
        _rate_limit_store[ip] = []
    # 计算最近一分钟请求数
    total = sum(c for _, c in _rate_limit_store[ip])
    if total >= _RATE_LIMIT_PER_MIN:
        logger.warning(f"[RATE-LIMIT] {ip} 超过频率限制 ({total}/min)")
        return openai_error("请求过于频繁，请稍后再试", err_type="rate_limit_error", status=429)
    _rate_limit_store[ip].append((now, 1))

# 全局单例
vector_kb: Optional[VectorKnowledgeBase] = None
teaching_system: Optional[TeachingSystem] = None
living_field: Optional[LivingInfoField] = None


# ==================== 辅助函数 ====================

def extract_files_from_request(data: Dict[str, Any]):
    files_content: List[str] = []
    all_text_parts: List[str] = []
    messages = data.get('messages', []) if isinstance(data, dict) else []

    # 收集所有 user 消息文本（保持对话连续性，跳过中间层注入的文件消息和OpenWebUI自动任务）
    _FILE_INJECT_MARKER = "【新文件 ·"
    _AUTO_MARKERS = {'### Task:', '### 任务:', 'Generate a concise', 'Generate 1-3 broad tags',
                     'Analyze the chat history', 'Create a title', 'Summarize this', 'Generate title'}
    for m in messages:
        if not isinstance(m, dict):
            continue
        if m.get('role') != 'user':
            continue
        content = m.get('content', '')
        # 跳过中间层之前注入的文件消息
        if isinstance(content, str) and content.startswith(_FILE_INJECT_MARKER):
            continue
        # 跳过OpenWebUI自动任务消息
        if isinstance(content, str) and any(content.strip().startswith(marker) for marker in _AUTO_MARKERS):
            continue
        if isinstance(content, str) and content.strip():
            all_text_parts.append(content.strip())
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get('type') == 'text':
                    txt = item.get('text', '').strip()
                    if txt and not any(txt.startswith(marker) for marker in _AUTO_MARKERS):
                        all_text_parts.append(txt)

    # 只从最后一条 user 消息中提取文件内容（避免历史中的旧文件被重复提取）
    last_user_msg = None
    for m in reversed(messages):
        if isinstance(m, dict) and m.get('role') == 'user':
            last_user_msg = m
            break

    if last_user_msg:
        content = last_user_msg.get('content', '')
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                itype = item.get('type', '')
                if itype in ('file', 'file_url', 'document', 'document_url', 'image_url'):
                    info = item.get(itype, item)
                    if isinstance(info, dict):
                        fname = info.get('name', info.get('filename', info.get('title', 'uploaded')))
                        fcontent = info.get('content', info.get('text', info.get('document', '')))
                        if not fcontent:
                            file_url_obj = info.get('url', {})
                            if isinstance(file_url_obj, dict):
                                fcontent = file_url_obj.get('content', '')
                            elif isinstance(file_url_obj, str) and file_url_obj.startswith('data:'):
                                import base64
                                try:
                                    parts = file_url_obj.split(',', 1)
                                    if len(parts) == 2:
                                        fcontent = base64.b64decode(parts[1]).decode('utf-8', errors='replace')
                                except Exception as e:
                                    logger.debug(f"[FILES] base64解码失败: {e}")
                        if isinstance(fcontent, str) and fcontent:
                            files_content.append(
                                f"--- 文件: {fname} ---\n{fcontent[:100000]}\n--- 文件结束 ---"
                            )
                            logger.info(f"[FILES] 提取 {fname}: {len(fcontent)} 字符")

    # 请求顶层与 metadata 中的文件
    for key in ('files', 'attachments', 'documents', 'uploads'):
        for f in data.get(key, []) or []:
            if isinstance(f, dict):
                fname = f.get('name', f.get('filename', 'unknown'))
                fcontent = f.get('content', f.get('text', f.get('document', '')))
                if isinstance(fcontent, str) and fcontent:
                    files_content.append(f"--- 文件: {fname} ---\n{fcontent[:100000]}\n--- 文件结束 ---")
    meta = data.get('metadata', {}) or {}
    if not meta:
        meta = data.get('meta', {}) or {}
    if isinstance(meta, dict):
        for key in ('files', 'attachments', 'documents', 'uploads'):
            for f in meta.get(key, []) or []:
                if isinstance(f, dict):
                    fname = f.get('name', f.get('filename', 'unknown'))
                    fcontent = f.get('content', f.get('text', ''))
                    if isinstance(fcontent, str) and fcontent:
                        files_content.append(f"--- 文件: {fname} ---\n{fcontent[:100000]}\n--- 文件结束 ---")

    combined = " ".join(all_text_parts)

    auto_markers = [
        '### Task:', '### 任务:', 'Generate a concise', 'Generate 1-3 broad tags',
        'Analyze the chat history', 'Create a title', 'Summarize this', 'Generate title'
    ]
    is_auto = any(marker in combined for marker in auto_markers)

    if is_auto:
        clean = combined[:500]
    elif len(combined) > 2000 and not files_content:
        # 用户粘贴了长文本：不提取文件内容，直接保留原始消息
        # 原始消息已在 clean_messages 中完整保留，无需重复注入
        # 只提取简短指令用于向量搜索
        lines = combined.split('\n')
        instr = []
        for i, line in enumerate(lines[:10]):
            if line.strip() and len(line) < 200 and not line.startswith('#'):
                instr.append(line)
            elif line.strip() and i < 3:
                continue
            elif line.strip():
                break
        clean = " ".join(instr)[:500] if instr else combined[:500]
    else:
        # 优先用最后一条用户消息（最相关），fallback到combined
        last_msg = all_text_parts[-1] if all_text_parts else ""
        clean = last_msg[:500] if last_msg else (combined[:500] if combined else "")

    if not clean and files_content:
        clean = "请分析上传的文件内容"

    # 文件引用解析
    if not files_content and clean:
        patterns = [
            r"\(\s*['\"]\s*['\"]\s*,\s*['\"](.+?)['\"]\s*\)",
            r"\(\s*['\"](.+?)['\"]\s*\)",
            r"\[文件\]\s*(.+)",
        ]
        for pat in patterns:
            m = re.search(pat, clean)
            if m:
                hint = m.group(1).strip()
                found = find_file_by_reference(hint, UPLOAD_FOLDER)
                if found:
                    files_content.append(
                        f"--- 文件引用解析: {hint} ---\n{found[:50000]}\n--- 文件结束 ---"
                    )
                break

    return "\n\n".join(files_content), clean, is_auto


def _derive_session_id(data: Dict[str, Any]) -> str:
    """优先使用 Open WebUI 传来的 session_id，而非从内容 hash 派生"""
    for key in ('session_id', 'chat_id', 'conversation_id'):
        sid = data.get(key, '')
        if sid and isinstance(sid, str) and len(sid) > 4:
            return sid
    meta = data.get('metadata', {}) or data.get('meta', {}) or {}
    for key in ('session_id', 'chat_id', 'conversation_id'):
        sid = meta.get(key, '')
        if sid and isinstance(sid, str) and len(sid) > 4:
            return sid
    msgs = data.get('messages', [])
    first_user = ""
    last_user = ""
    for m in msgs:
        if isinstance(m, dict) and m.get('role') == 'user':
            c = m.get('content', '')
            if isinstance(c, str):
                c = c[:200]
            elif isinstance(c, list):
                c = json.dumps(c, ensure_ascii=False)[:200]
            else:
                c = str(c)[:200]
            if not first_user:
                first_user = c
            last_user = c
    payload = f"{first_user}|{last_user}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _finalize_turn(
    session_id: str,
    user_input: str,
    response_text: str,
    eta_before: float,
    articles_content: str,
    loaded_chunks: List[str],
    usage: Dict[str, int] = None,
    request_model: str = None,
    finish_reason: str = "stop"
) -> Dict[str, Any]:
    """
    v10 增强：
    - 在 finalize 阶段检查AI回复是否体现了某条纠正
    - 如果体现了，增加该纠正的 trust_level 和 applied_count
    - 更新 ChromaDB 中的纠正记录
    """
    # 从 LivingInfoField 获取历史查询和时间间隔
    history_queries = living_field.get_history_queries(session_id)
    delta_seconds = living_field.get_history_delta_seconds(session_id)

    # 计算回复的共扼谱几何术语密度（自指反馈信号）
    geo_density = compute_geo_density(response_text)

    # 调用 update_eta_living，传入 history_queries、delta_seconds、geo_density
    eta_after, metrics = update_eta_living(
        eta_before, response_text, user_input, session_id, vector_kb,
        history_queries=history_queries,
        delta_seconds=delta_seconds,
        geo_density=geo_density
    )

    # 检查相位标记（传入 session_id 以更新 LivingInfoField）
    check_phase_marker(eta_before, eta_after, user_input, session_id)

    # 更新 LivingInfoField（替代 set_eta_state）
    living_field.update_eta(session_id, eta_after)

    # 添加到历史记录
    living_field.add_to_history(session_id, user_input, response_text)

    # 记录 DeepSeek prompt cache 命中率
    if usage:
        _pt = usage.get('prompt_tokens', 0)
        _ch = usage.get('prompt_cache_hit_tokens', 0)
        _cm = usage.get('prompt_cache_miss_tokens', 0)
        if _pt > 0:
            _rate = _ch / _pt * 100
            logger.info(f"[CACHE] prompt={_pt} hit={_ch} miss={_cm} rate={_rate:.1f}% model={request_model or GAI_MODEL}")

    # 保存对话记录到内存列表（服务重启后丢失，learned 集合在 ChromaDB 中持久化）
    save_conversation(
        session_id, user_input, response_text,
        eta_before, eta_after, get_strategy(eta_before),
        "", ",".join(loaded_chunks), metrics
    )

    # 学习闭环：如果回复质量好，存入 learned 集合
    coherence = metrics.get('coherence', 0.0)
    if (vector_kb
        and vector_kb.is_initialized
        and coherence > LEARN_COHERENCE_THRESHOLD
        and len(response_text) > LEARN_MIN_LENGTH):
        learn_score = coherence
        vector_kb.learn(user_input, response_text, learn_score)
        logger.info(
            f"[LEARN] 高质量对话已存入学习库 | "
            f"coherence={coherence:.3f} | length={len(response_text)}"
        )

    # 自指反馈环 - 批量提取关键论断并存入向量库（一次性写入，避免逐条卡顿）
    propositions = extract_key_propositions(response_text)
    if propositions and vector_kb and vector_kb.is_initialized:
        vector_kb.learn_propositions_batch(propositions, min(coherence * (1.0 + geo_density), 1.0))
        logger.info(
            f"[SELF-REF] 提取 {len(propositions)} 个关键论断 | "
            f"geo_density={geo_density:.4f}"
        )

    # v10 新增：检查纠正是否被应用，更新信任等级
    corrections_applied = []
    if teaching_system and vector_kb and vector_kb.is_initialized:
        try:
            corrections_applied = teaching_system.check_and_update_corrections(response_text)
            if corrections_applied:
                logger.info(
                    f"[TEACH-FINALIZE] {len(corrections_applied)} 条纠正被成功应用"
                )
        except Exception as e:
            logger.error(f"[TEACH-FINALIZE] 检查纠正应用失败: {e}")

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request_model or GAI_MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "logprobs": None,
            "finish_reason": finish_reason
        }],
        "usage": usage or {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        },
        "system_fingerprint": f"fp_{hashlib.md5((request_model or GAI_MODEL).encode()).hexdigest()[:8]}_{int(time.time()) % 86400}",
    }


# ==================== 文章预览页 ====================

def _inline(text):
    """行内Markdown渲染：粗体、斜体、行内代码、链接"""
    import html as _html
    import re as _re
    text = _html.escape(text)
    text = _re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = _re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = _re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


@app.route('/preview/<path:filename>')
def preview_article(filename):
    """文章预览页（Markdown渲染为HTML + KaTeX公式）"""
    import html as _html
    import re as _re
    fpath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(fpath):
        # 递归搜索子目录
        try:
            from tools import _find_article_recursive
            rel_path = _find_article_recursive(filename)
            if rel_path:
                fpath = os.path.join(UPLOAD_FOLDER, rel_path)
                filename = rel_path
        except ImportError:
            pass
    if not os.path.exists(fpath):
        # 最后尝试：在根目录模糊匹配
        if os.path.exists(UPLOAD_FOLDER):
            matches = [f for f in os.listdir(UPLOAD_FOLDER) if filename in f]
            if len(matches) == 1:
                fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                filename = matches[0]
    if not os.path.exists(fpath):
        return "文件不存在", 404
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    # 保护LaTeX公式
    _latex_blocks = []
    def _protect(m):
        idx = len(_latex_blocks)
        _latex_blocks.append(m.group(0))
        return f'\x00L{idx}\x00'
    content = _re.sub(r'\$\$(.+?)\$\$', _protect, content, flags=_re.DOTALL)
    content = _re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _protect, content)
    # Markdown渲染
    lines = content.split('\n')
    html_parts = []
    in_code = False
    in_table = False
    in_ul = False
    in_ol = False
    for line in lines:
        # 代码块
        if line.startswith('```'):
            if in_code:
                html_parts.append('</code></pre>')
                in_code = False
            else:
                if in_ul: html_parts.append('</ul>'); in_ul = False
                if in_ol: html_parts.append('</ol>'); in_ol = False
                html_parts.append('<pre style="background:#1a1a1a;padding:12px;border-radius:8px;overflow-x:auto;font-size:13px;border:1px solid #333;"><code>')
                in_code = True
            continue
        if in_code:
            html_parts.append(_html.escape(line))
            continue
        stripped = line.strip()
        # 空行
        if not stripped:
            if in_ul: html_parts.append('</ul>'); in_ul = False
            if in_ol: html_parts.append('</ol>'); in_ol = False
            if in_table: html_parts.append('</table>'); in_table = False
            continue
        # 标题
        if stripped.startswith('######'):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<h6>{_inline(stripped[6:].strip())}</h6>')
        elif stripped.startswith('#####'):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<h5>{_inline(stripped[5:].strip())}</h5>')
        elif stripped.startswith('####'):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<h4>{_inline(stripped[4:].strip())}</h4>')
        elif stripped.startswith('###'):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<h3>{_inline(stripped[3:].strip())}</h3>')
        elif stripped.startswith('##'):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<h2>{_inline(stripped[2:].strip())}</h2>')
        elif stripped.startswith('# '):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<h1>{_inline(stripped[2:].strip())}</h1>')
        # 表格
        elif '|' in stripped and stripped.startswith('|'):
            if in_ul: html_parts.append('</ul>'); in_ul = False
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if all(set(c) <= set('-: ') for c in cells):
                continue  # 分隔行跳过
            if not in_table:
                html_parts.append('<table>')
                in_table = True
            tag = 'th' if not in_table or (html_parts[-1] == '<table>') else 'td'
            # 简单判断是否第一行（表头）
            if '<table>' in html_parts[-1] if html_parts else False:
                tag = 'th'
            row = ''.join(f'<{tag}>{_inline(c)}</{tag}>' for c in cells)
            html_parts.append(f'<tr>{row}</tr>')
        else:
            if in_table: html_parts.append('</table>'); in_table = False
            # 无序列表
            if stripped.startswith(('- ', '* ', '• ')):
                if not in_ul:
                    html_parts.append('<ul>')
                    in_ul = True
                html_parts.append(f'<li>{_inline(stripped[2:])}</li>')
            # 有序列表
            elif _re.match(r'^\d+[\.\)]\s', stripped):
                if not in_ol:
                    html_parts.append('<ol>')
                    in_ol = True
                text = _re.sub(r'^\d+[\.\)]\s+', '', stripped)
                html_parts.append(f'<li>{_inline(text)}</li>')
            else:
                if in_ul: html_parts.append('</ul>'); in_ul = False
                if in_ol: html_parts.append('</ol>'); in_ol = False
                html_parts.append(f'<p>{_inline(stripped)}</p>')
    if in_code: html_parts.append('</code></pre>')
    if in_ul: html_parts.append('</ul>')
    if in_ol: html_parts.append('</ol>')
    if in_table: html_parts.append('</table>')
    # 恢复LaTeX
    html_body = '\n'.join(html_parts)
    for i, block in enumerate(_latex_blocks):
        html_body = html_body.replace(f'\x00L{i}\x00', block)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_html.escape(filename)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {{delimiters: [{{left: '$$', right: '$$', display: true}}, {{left: '$', right: '$', display: false}}], throwOnError: false}});"></script>
<style>
body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 20px; max-width: 900px; margin: 0 auto; line-height: 1.8; }}
h1 {{ color: #4fc3f7; border-bottom: 1px solid #333; padding-bottom: 10px; }}
h2 {{ color: #81d4fa; margin-top: 30px; }}
h3 {{ color: #b3e5fc; }}
h4 {{ color: #e1f5fe; }}
h5,h6 {{ color: #ccc; }}
strong {{ color: #fff; }}
pre {{ margin: 10px 0; }}
code {{ background: #1a1a1a; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
a {{ color: #4fc3f7; }}
.back {{ color: #888; font-size: 14px; margin-bottom: 20px; display: block; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #333; padding: 8px 12px; text-align: left; }}
th {{ background: #1a1a1a; color: #4fc3f7; }}
ul, ol {{ padding-left: 20px; }}
li {{ margin: 4px 0; }}
.katex {{ color: #fff; }}
</style>
</head>
<body>
<a class="back" href="javascript:history.back()">← 返回</a>
{html_body}
</body>
</html>'''


# ==================== API路由 ====================

@app.route('/health', methods=['GET'])
def health_check():
    status = {
        "status": "ok",
        "version": VERSION,
        "build_date": BUILD_DATE,
        "description": "教学反馈版（无MySQL依赖）",
        "timestamp": datetime.now().isoformat(),
        "model": GAI_MODEL,
        "vector_kb_initialized": vector_kb is not None and vector_kb.is_initialized,
        "articles_count": vector_kb.articles_count if vector_kb else 0,
        "learned_count": vector_kb.learned_count if vector_kb else 0,
        "corrections_count": vector_kb.corrections_count if vector_kb else 0,
        "antipatterns_count": vector_kb.antipatterns_count if vector_kb else 0,
        "patches_count": vector_kb.patches_count if vector_kb else 0,
        "total_docs": vector_kb.total_docs if vector_kb else 0,
        "db_mode": "内存（无MySQL依赖）",
        "upload_folder": UPLOAD_FOLDER,
        "living_sessions": living_field.get_all_sessions_count(),
        "teaching_system": "已启用" if teaching_system else "未初始化",
    }
    return jsonify(status)


@app.route('/v1/index/status', methods=['GET'])
def index_status():
    if not vector_kb:
        return openai_error("向量知识库未初始化")
    return jsonify({
        "total_chunks": vector_kb.total_docs,
        "articles_count": vector_kb.articles_count,
        "learned_count": vector_kb.learned_count,
        "corrections_count": vector_kb.corrections_count,
        "antipatterns_count": vector_kb.antipatterns_count,
        "patches_count": vector_kb.patches_count,
        "upload_folder": UPLOAD_FOLDER,
        "chroma_db_dir": CHROMA_DB_DIR,
        "embedding_model": GAI_EMBEDDING_MODEL,
    })


@app.route('/v1/index/rebuild', methods=['POST'])
def index_rebuild():
    global vector_kb
    if not vector_kb:
        vector_kb = VectorKnowledgeBase(CHROMA_DB_DIR)
        vector_kb.initialize()
    diag = vector_kb.build_index(UPLOAD_FOLDER)
    return jsonify({
        "success": vector_kb.articles_count > 0,
        "diagnostics": diag,
        "total_chunks": vector_kb.articles_count,
    })


@app.route('/v1/openapi.json', methods=['GET'])
@app.route('/v1/openapi.json/openapi.json', methods=['GET'])
def openapi_spec():
    """返回 OpenAPI spec，供 Open WebUI 导入为工具。"""
    return jsonify(OPENAPI_SPEC)


@app.route('/v1/personal', methods=['GET'])
def personal_read():
    """读取个人数据库。"""
    return jsonify(personal_db)


@app.route('/v1/personal', methods=['PUT'])
def personal_write():
    """写入个人数据库。"""
    data = request.get_json(force=True, silent=True) or {}
    category = data.get("category", "")
    content = data.get("content", "")
    result = execute_tool_call("personal_write", {"category": category, "content": content})
    return jsonify({"result": result})


@app.route('/v1/chat/history', methods=['GET'])
def chat_history():
    """查询 Open WebUI 历史对话列表。"""
    keyword = request.args.get("keyword", "")
    limit = int(request.args.get("limit", "5"))
    result = execute_tool_call("chat_history", {"keyword": keyword, "limit": str(limit)})
    return jsonify({"result": result})


@app.route('/v1/chat/<chat_id>', methods=['GET'])
def chat_read(chat_id):
    """读取指定对话的完整内容。"""
    result = execute_tool_call("chat_read", {"chat_id": chat_id})
    return jsonify({"result": result})


@app.route('/v1/chat/<chat_id>/export', methods=['GET'])
def chat_export(chat_id):
    """导出指定对话为 Markdown 文件。"""
    result = execute_tool_call("chat_read", {"chat_id": chat_id})
    # 将对话转换为 Markdown 格式
    lines = [f"# 对话导出\n"]
    if isinstance(result, str):
        try:
            data = json.loads(result)
            title = data.get("title", chat_id)
            messages = data.get("messages", [])
            lines[0] = f"# {title}\n"
            for msg in messages:
                role = msg.get("role", "?")
                content = msg.get("content", "")
                if isinstance(content, list):
                    # 多模态消息，提取文本
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    content = "\n".join(text_parts)
                if not content or not content.strip():
                    continue
                if role == "user":
                    lines.append(f"## 用户\n\n{content}\n")
                elif role == "assistant":
                    lines.append(f"## 助手\n\n{content}\n")
                elif role == "system":
                    lines.append(f"<!-- 系统: {content[:100]}... -->\n")
        except (json.JSONDecodeError, TypeError):
            lines.append(result)
    md_content = "\n".join(lines)
    return Response(md_content, mimetype="text/markdown", headers={
        "Content-Disposition": f"attachment; filename=chat_{chat_id[:8]}.md"
    })


@app.route('/v1/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return openai_error("请求中没有文件字段 'file'", err_type="invalid_request_error", status=400)
    file = request.files['file']
    if file.filename == '':
        return openai_error("未选择文件", err_type="invalid_request_error", status=400)
    if not allowed_file(file.filename):
        return openai_error(f"不支持的文件格式: {file.filename}", err_type="invalid_request_error", status=400)

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    logger.info(f"[UPLOAD] 文件已保存: {filepath} ({file_size} bytes)")

    text_content, parse_ok = extract_text_from_file(filepath)
    if not parse_ok:
        return openai_error(f"文件解析失败: {filename} (PDF需要PyPDF2, DOCX需要python-docx)")

    # 重建向量索引
    global vector_kb
    if vector_kb and vector_kb.is_initialized:
        diag = vector_kb.build_index(UPLOAD_FOLDER)

    return jsonify({
        "success": True,
        "filename": filename,
        "saved_to": filepath,
        "file_size": file_size,
        "text_length": len(text_content),
        "parse_ok": parse_ok,
        "index_rebuilt": vector_kb.articles_count > 0 if vector_kb else False,
        "total_chunks": vector_kb.total_docs if vector_kb else 0,
        "diagnostics": diag if vector_kb else {}
    })


@app.route('/v1/files', methods=['GET'])
def list_files():
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for fname in sorted(os.listdir(UPLOAD_FOLDER)):
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.isfile(fpath):
                files.append({
                    "name": fname,
                    "size": os.path.getsize(fpath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                })
    return jsonify({"upload_folder": UPLOAD_FOLDER, "total_files": len(files), "files": files})


@app.route('/v1/files/<filename>', methods=['GET'])
def read_file(filename):
    """读取 articles 目录中的指定文件内容。"""
    fpath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(fpath):
        # 模糊匹配
        if os.path.exists(UPLOAD_FOLDER):
            matches = [f for f in os.listdir(UPLOAD_FOLDER) if filename in f]
            if len(matches) == 1:
                fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                filename = matches[0]
            elif len(matches) > 1:
                return openai_error(f"找到多个匹配文件: {matches}", err_type="invalid_request_error", status=400)
            else:
                return openai_error(f"文件 '{filename}' 不存在", err_type="not_found_error", status=404)
        else:
            return openai_error("文章目录不存在")
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"filename": filename, "content": content, "size": len(content)})
    except Exception as e:
        return openai_error(str(e))


@app.route('/v1/files/<filename>', methods=['PUT'])
def write_file(filename):
    """写入或修改 articles 目录中的文件。"""
    data = request.get_json(force=True, silent=True) or {}
    content = data.get('content', '')
    if not content:
        return openai_error("缺少 content 字段", err_type="invalid_request_error", status=400)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    fpath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        # 增量索引
        global vector_kb
        if vector_kb and vector_kb.is_initialized:
            vector_kb.index_single_file(fpath)
        return jsonify({"success": True, "filename": filename, "size": len(content)})
    except Exception as e:
        return openai_error(str(e))


@app.route('/v1/models', methods=['GET'])
@app.route('/openai/models', methods=['GET'])
@app.route('/openai/models/<path:_dummy>', methods=['GET'])  # 0.9.5 兼容：/openai/models/0 等
def list_models():
    def _model_entry(mid):
        owner = "deepseek" if "deepseek" in mid.lower() else "openai" if "gpt" in mid.lower() else "system"
        return {"id": mid, "object": "model", "created": 1700000000 + hash(mid) % 86400, "owned_by": owner}
    _models = [
        _model_entry(GAI_MODEL),
        _model_entry(GAI_MODEL_LITE),
        _model_entry(GAI_MODEL_VISION),
    ]
    # 添加额外模型
    for m_id in EXTRA_MODELS:
        _models.append(_model_entry(m_id))
    # 去重（如果多个配置指向同一模型）
    _seen = set()
    _unique = []
    for m in _models:
        if m["id"] not in _seen:
            _seen.add(m["id"])
            _unique.append(m)
    return jsonify({"object": "list", "data": _unique})


# ==================== Embeddings 端点（带缓存） ====================

_embedding_cache = {}  # {hash(input+model): response_data}
_EMBEDDING_CACHE_MAX = 500  # 最多缓存500条


@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    """OpenAI 兼容的 embeddings 端点，带内存缓存"""
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return openai_error("Invalid request body", err_type="invalid_request_error", status=400)
    if not data.get('input'):
        return openai_error("Missing required parameter: input", err_type="invalid_request_error", status=400)
    # 缓存检查
    model = data.get('model', GAI_EMBEDDING_MODEL)
    input_data = data['input']
    cache_key = hashlib.md5((json.dumps(input_data, sort_keys=True) + model).encode()).hexdigest()
    if cache_key in _embedding_cache:
        return jsonify(_embedding_cache[cache_key])
    try:
        client = openai.OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)
        resp = client.embeddings.create(model=model, input=input_data)
        result = resp.model_dump()
        # 写入缓存
        if len(_embedding_cache) >= _EMBEDDING_CACHE_MAX:
            # 简单清理：删除最早的 100 条
            keys_to_remove = list(_embedding_cache.keys())[:100]
            for k in keys_to_remove:
                del _embedding_cache[k]
        _embedding_cache[cache_key] = result
        return jsonify(result)
    except Exception as e:
        return openai_error(f"Embedding error: {e}", status=500)


# ==================== 向量库管理 API 路由 ====================

@app.route('/v1/vector/status', methods=['GET'])
def vector_status():
    """返回向量库状态（articles数量、learned数量、教学集合数量）"""
    if not vector_kb:
        return openai_error("向量知识库未初始化")
    return jsonify(vector_kb.get_status())


@app.route('/v1/vector/learned/clear', methods=['POST'])
def vector_learned_clear():
    """清空学习库"""
    if not vector_kb:
        return openai_error("向量知识库未初始化")
    result = vector_kb.clear_learned()
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code


@app.route('/v1/vector/rebuild', methods=['POST'])
def vector_rebuild():
    """重建文章索引"""
    global vector_kb
    if not vector_kb:
        vector_kb = VectorKnowledgeBase(CHROMA_DB_DIR)
        if not vector_kb.initialize():
            return openai_error("ChromaDB 初始化失败")
    diag = vector_kb.build_index(UPLOAD_FOLDER)
    return jsonify({
        "success": vector_kb.articles_count > 0,
        "diagnostics": diag,
        "articles_count": vector_kb.articles_count,
        "learned_count": vector_kb.learned_count,
        "total_docs": vector_kb.total_docs,
    })


# ==================== 活体信息场 API 路由 ====================

@app.route('/v1/living/status', methods=['GET'])
def living_status():
    """返回活体信息场状态"""
    return jsonify({
        "sessions_count": living_field.get_all_sessions_count(),
        "description": "活体信息场：纯内存 eta 状态管理，不依赖外部数据库",
    })


@app.route('/v1/living/sessions', methods=['GET'])
def living_sessions():
    """返回所有活跃 session 的摘要信息"""
    sessions_summary = {}
    for sid, info in living_field._sessions.items():
        sessions_summary[sid] = {
            "eta": round(info['eta'], 4),
            "max_eta": round(info['max_eta'], 4),
            "markers": info['markers'],
            "history_count": len(info['history']),
            "last_time": datetime.fromtimestamp(info['last_time']).isoformat() if info['last_time'] else None,
        }
    return jsonify({
        "total_sessions": len(sessions_summary),
        "sessions": sessions_summary,
    })


@app.route('/v1/living/session/<session_id>', methods=['GET'])
def living_session_detail(session_id: str):
    """返回指定 session 的详细信息"""
    info = living_field.get_session_info(session_id)
    return jsonify({"session_id": session_id, "info": info})


# ==================== v10 新增：教学系统 API 路由 ====================

@app.route('/v1/teach/correct', methods=['POST'])
def teach_correct():
    """
    纠正 API：用户纠正系统错误。
    请求体：
    {
        "wrong": "错误内容",
        "correct": "正确解释",
        "reason": "原因（可选）",
        "context": "对话上下文（可选）"
    }
    """
    if not teaching_system:
        return openai_error("教学系统未初始化")

    data = request.get_json(force=True)
    wrong = data.get('wrong', '').strip()
    correct = data.get('correct', '').strip()
    reason = data.get('reason', '').strip()
    context = data.get('context', '').strip()
    session_id = data.get('session_id', '').strip()
    article_id = data.get('article_id', '').strip()
    trust = float(data.get('trust', 0.5))

    result = teaching_system.add_correction(
        wrong=wrong, correct=correct, reason=reason,
        context=context, session_id=session_id,
        article_id=article_id, trust=trust
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/rollback', methods=['POST'])
def teach_rollback():
    """
    回滚 API：撤销一个纠正对 articles 向量集合的修改。
    请求体：
    {
        "correction_id": "corr_xxx"  （从 teach_correct 返回的 correction_id）
    }
    """
    if not vector_kb or not vector_kb.is_initialized:
        return openai_error("向量库未初始化")

    data = request.get_json(force=True)
    correction_id = data.get('correction_id', '').strip()

    if not correction_id:
        return openai_error("correction_id 不能为空", err_type="invalid_request_error", status=400)

    result = vector_kb.rollback_correction(correction_id)
    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/antipattern', methods=['POST'])
def teach_antipattern():
    """
    反模式 API：标记不应出现的回复模式。
    请求体：
    {
        "pattern": "模式文本",
        "description": "描述",
        "severity": "high/medium/low"
    }
    """
    if not teaching_system:
        return openai_error("教学系统未初始化")

    data = request.get_json(force=True)
    pattern = data.get('pattern', '').strip()
    description = data.get('description', '').strip()
    severity = data.get('severity', 'medium').strip().lower()

    result = teaching_system.add_antipattern(
        pattern=pattern, description=description, severity=severity
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/patch', methods=['POST'])
def teach_patch():
    """
    知识补丁 API：直接补充共扼谱几何知识。
    请求体：
    {
        "topic": "主题",
        "content": "正确解释",
        "source": "来源"
    }
    """
    if not teaching_system:
        return openai_error("教学系统未初始化")

    data = request.get_json(force=True)
    topic = data.get('topic', '').strip()
    content = data.get('content', '').strip()
    source = data.get('source', '').strip()

    result = teaching_system.add_patch(
        topic=topic, content=content, source=source
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/stats', methods=['GET'])
def teach_stats():
    """
    教学统计 API：返回纠正数、反模式数、知识补丁数、各信任等级分布。
    """
    if not teaching_system:
        return openai_error("教学系统未初始化")

    stats = teaching_system.get_stats()
    return jsonify(stats)


@app.route('/v1/teach/history', methods=['GET'])
def teach_history():
    """
    教学历史 API：返回所有教学记录，支持分页。
    查询参数：page（页码，默认1）、per_page（每页条数，默认20）
    """
    if not teaching_system:
        return openai_error("教学系统未初始化")

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # 限制每页最多100条

    history = teaching_system.get_history(page=page, per_page=per_page)
    return jsonify(history)


# ==================== 核心 chat completions 端点 ====================

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # API Key 认证（OpenAI 标准兼容）
    _auth = request.headers.get('Authorization', '')
    _api_keys = os.getenv('GAI_API_KEYS', '')
    if _api_keys:
        _allowed_keys = [k.strip() for k in _api_keys.split(',') if k.strip()]
        _provided_key = _auth.replace('Bearer ', '').strip() if _auth.startswith('Bearer ') else ''
        if _provided_key and _allowed_keys and _provided_key not in _allowed_keys:
            return openai_error("Invalid API key", "invalid_request_error", 401)
    # 如果 GAI_API_KEYS 未设置或为空，则不进行认证（向后兼容）

    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return openai_error("Invalid request body", err_type="invalid_request_error", status=400)
    if not data.get('messages') or not isinstance(data['messages'], list):
        return openai_error("Missing or invalid 'messages' field", err_type="invalid_request_error", status=400)
    stream = data.get('stream', False)

    # 子代理模式（AutoGen 等外部智能体调用）：跳过工具注入，直接文本回复
    # 外部智能体有自己的多轮对话与角色分工，不需要中间层再触发自主工具循环
    _is_subagent = request.headers.get('X-GAI-MODE', '') == 'subagent'
    if _is_subagent:
        logger.info(f"[SUBAGENT] 子代理模式：跳过工具注入，直接文本回复")

    # ===== 请求诊断日志 =====
    _debug_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        _debug_path = os.path.join(_debug_dir, 'request_debug.jsonl')
        with open(_debug_path, 'a', encoding='utf-8') as _f:
            _safe = json.dumps(data, ensure_ascii=False, default=str)[:50000]
            _f.write(f"{datetime.now().isoformat()} | {_safe}\n")
    except Exception as e:
        logger.debug(f"[DEBUG] 请求诊断日志写入失败: {e}")

    # 深度诊断最后一条 user 消息
    for m in reversed(data.get('messages', [])):
        if isinstance(m, dict) and m.get('role') == 'user':
            _c = m.get('content')
            if isinstance(_c, str):
                logger.info(f"[DEBUG] 最后user消息: str, len={len(_c)}, 前200字={_c[:200]}")
            elif isinstance(_c, list):
                logger.info(f"[DEBUG] 最后user消息: list, 元素数={len(_c)}, types={[i.get('type','?') for i in _c if isinstance(i,dict)]}")
            elif _c is None:
                logger.info(f"[DEBUG] 最后user消息: None")
            break

    files_content, clean_query, is_auto_request = extract_files_from_request(data)

    logger.info(f"[DEBUG] extract_files结果: files_content={len(files_content)}字符, clean_query='{clean_query[:100]}'")

    # 如果 clean_query 太长（被文件内容污染），用最后一条 user 消息的短文本替代
    if len(clean_query) > 300:
        for m in reversed(data.get('messages', [])):
            if isinstance(m, dict) and m.get('role') == 'user':
                c = m.get('content', '')
                if isinstance(c, str):
                    # 取最后一行或最后200字符
                    lines = [l.strip() for l in c.split('\n') if l.strip()]
                    short = lines[-1] if lines else c
                    if len(short) > 200:
                        short = short[:200]
                    # 排除明显是文件内容的长文本
                    if len(short) < 300 and not short.startswith('#') and not short.startswith('>'):
                        clean_query = short
                        break
                elif isinstance(c, list):
                    for item in c:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            txt = item.get('text', '').strip()
                            if txt and len(txt) < 300:
                                clean_query = txt
                                break

    # 始终检查 uploads 目录，如果有新上传文件则覆盖历史消息中的旧文件
    # 但自动请求（标题生成、搜索查询）不注入文件，避免浪费和重复标记
    ow_content = ""
    ow_injected_info = []
    if not is_auto_request:
        ow_content, ow_injected_info = scan_openwebui_recent_uploads()
        if ow_content:
            files_content = ow_content
            logger.info(f"[OPENWEBUI] 从uploads目录补充了 {len(ow_content)} 字符的文件内容")

    if not clean_query:
        clean_query = "请继续"

    session_id = data.get('session_id', '') or _derive_session_id(data)

    # token 节省整改 A：按查询内容初判任务模式（编程类放宽 shell 探索预算，仅首次生效）
    try:
        if any(k in clean_query.lower() for k in _CODING_KEYWORDS):
            init_session_mode(session_id, 'coding')
            logger.info(f"[SHELL-BUDGET] 查询命中编程关键词，会话 {session_id[:16]} → coding 模式")
        else:
            init_session_mode(session_id, 'derive')
    except Exception:
        pass

    # 从 LivingInfoField 获取 eta，而非 get_eta_state()
    # 如果是新 session（LivingInfoField 中不存在），用输入文本的软模共振公式初始化
    session_info = living_field.get_session_info(session_id)
    if session_info['last_time'] is None:
        # 新 session，从输入文本计算初始 eta
        eta_before = living_field.init_eta_from_input(session_id, clean_query)
    else:
        eta_before = living_field.get_eta(session_id)

    max_eta = session_info['max_eta']
    markers = session_info['markers']
    stage = get_stage(eta_before)
    strategy = get_strategy(eta_before)

    # 向量语义检索（从 articles + learned 两个集合获取结果）
    articles_content = ""
    loaded_chunks: List[str] = []
    # 向量库未初始化/为空时会跳过检索分支，results 不会被赋值；若不用列表占位，
    # 后续 _workbench_gate(..., bool(results)) 会抛 UnboundLocalError 导致整请求 500。
    results: list = []
    logger.info(f"[VECTOR-DEBUG] vector_kb={vector_kb is not None}, initialized={vector_kb.is_initialized if vector_kb else 'N/A'}, total_docs={vector_kb.total_docs if vector_kb else 'N/A'}")
    try:
        if vector_kb and vector_kb.is_initialized and vector_kb.total_docs > 0:
            # 智能提取检索关键词：如果clean_query太长，提取核心术语
            search_query = clean_query
            if len(clean_query) > 100:
                # 提取文章编号（如 0.5, 0.2.1）和中文学术术语
                import re as _re2
                # 提取文章编号模式
                ids = _re2.findall(r'\b\d+(?:\.\d+)+\b', clean_query)
                # 提取中文术语（2-6字）
                terms = _re2.findall(r'[\u4e00-\u9fff]{2,6}', clean_query)
                # 组合：编号优先，然后取前5个术语
                search_parts = list(set(ids)) + list(set(terms))[:5]
                if search_parts:
                    search_query = ' '.join(search_parts)
                else:
                    search_query = clean_query[:100]
            # 多轮检索：三角度交叉搜索（原始查询 + 数学工具角度 + 文章编号角度）
            import re as _re2
            search_terms = _re2.findall(r'[\u4e00-\u9fff]{2,6}', clean_query)
            search_numbers = _re2.findall(r'\d+(?:\.\d+)*', clean_query)
            results_main = vector_kb.search(search_query, top_k=8)
            # 数学角度与跨领域角度仅在主查询召回不足时兜底执行，
            # 避免冗余 embedding 调用拖慢响应、稀释检索焦点
            results_math = []
            if len(results_main or []) < 5 and search_terms:
                results_math = vector_kb.search(
                    '公理 定理 引理 推导 证明 定义 假设 推论 ' + ' '.join(search_terms[:5]),
                    top_k=8
                )
            results_nums = []
            if search_numbers:
                results_nums = vector_kb.search(
                    '文章编号 ' + ' '.join(search_numbers[:3]),
                    top_k=6
                )
            # 跨领域关联搜索（找与问题同主题的前后文和对称概念），仅作最后兜底
            results_cross = []
            if (len(results_main or []) + len(results_math or [])) < 6 and search_terms:
                cross_query = '对称 对偶 逆 对应 变换 映射 相关 ' + ' '.join(search_terms[:3])
                results_cross = vector_kb.search(cross_query, top_k=4) or []
            # 合并去重（按 chunk_id 去重，保留距离最近的；无 id 的旧格式条目保留以防漏检）
            seen_ids = set()
            merged = []
            for r in (results_main or []) + (results_math or []) + (results_nums or []) + (results_cross or []):
                rid = r.get('id', '') or r.get('metadata', {}).get('chunk_id', '')
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    merged.append(r)
                elif not rid:
                    merged.append(r)
            merged.sort(key=lambda x: (1 if x.get('_skeleton') else 0,
                                       x.get('distance', 1.0)))
            # 推导类任务：引用图骨架增强（骨架文章 chunk 插到最前）
            _deriv_pat = re.compile(r'推导|证明|机制|来源|链条|如何|为什么|得出|导出|验证|完整|计算|统计|估算|求值|分析|推演')
            if _deriv_pat.search(clean_query) and merged:
                setattr(vector_kb, '_graph_max_hops', 2)  # 多跳推理：沿引用图向外扩展2层
                logger.info(f"[GRAPH-DIAG] 推导门控命中(clean_query含推导词) merged={len(merged)} -> enrich_with_graph")
                merged, _gchunks = vector_kb.enrich_with_graph(merged, search_query)
                if _gchunks:
                    logger.info(f"[VECTOR-GRAPH] 引用图骨架注入: {len(_gchunks)} 块")
                elif _deriv_pat.search(clean_query):
                    logger.info("[GRAPH-DIAG] enrich 返回空骨架，未注入")
            results = merged[:MAX_CHUNKS_PER_QUERY]
            logger.info(
                f"[VECTOR-MULTI] 四角度检索: main={len(results_main or [])}, "
                f"math={len(results_math or [])}, nums={len(results_nums or [])}, "
                f"cross={len(results_cross or [])}, merge={len(results)}"
            )
            article_fnames = set()
            if results:
                articles_content, loaded_chunks = vector_kb.get_formatted_results(results)
                # 提取所有检索到的文件名列表（用于让AI知道哪些文章存在）
                for r in results:
                    meta = r.get('metadata', {})
                    fname = meta.get('fname', '')
                    if fname:
                        article_fnames.add(fname)
                # 在参考资料顶部插入文件名索引（最多8个，节省token）
                if article_fnames:
                    fname_list = '\n'.join(sorted(article_fnames)[:8])
                    articles_content = f"【本次检索命中以下文章】\n{fname_list}\n\n{articles_content}"
            if not articles_content:
                logger.info(f"[VECTOR] 检索无结果: query='{clean_query[:80]}...', search='{search_query[:80]}', top_k={MAX_CHUNKS_PER_QUERY}, total_docs={vector_kb.total_docs}")
                # 防御性重试一次：embedding 偶发故障（限流/零向量）导致空结果时，短暂等待后重试主检索
                if vector_kb.is_initialized:
                    time.sleep(0.3)
                    _retry = vector_kb.search(search_query, top_k=8)
                    if _retry:
                        _retry_content, _retry_chunks = vector_kb.get_formatted_results(_retry)
                        if _retry_content:
                            articles_content = _retry_content
                            loaded_chunks = _retry_chunks
                            logger.info(f"[VECTOR] 重试检索成功: {len(_retry)} 条")
    except Exception as _vec_err:
        logger.error(f"[VECTOR] 检索块异常，降级重试: {_vec_err}")
        articles_content = ""
        try:
            _fallback = vector_kb.search(clean_query, top_k=MAX_CHUNKS_PER_QUERY)
            if _fallback:
                _content, _chunks = vector_kb.get_formatted_results(_fallback)
                if _content:
                    articles_content = _content
                    loaded_chunks = _chunks
                    logger.info(f"[VECTOR] 降级检索成功: {len(_fallback)} 条")
        except Exception as _vec_err2:
            logger.error(f"[VECTOR] 降级重试失败: {_vec_err2}")
    index_empty = not vector_kb.is_initialized or vector_kb.articles_count == 0
    search_no_result = not articles_content and vector_kb.is_initialized and vector_kb.articles_count > 0

    # v10 新增：从 corrections 和 patches 检索相关教学数据
    # 用 search_query 检索（与主向量检索同文本，命中 embedding 缓存，不产生额外 API 调用）
    teaching_section = ""
    if teaching_system:
        try:
            teaching_section = teaching_system.build_teaching_prompt_section(search_query if search_query else clean_query)
        except Exception as e:
            logger.error(f"[TEACH] 构建教学prompt段落失败: {e}")

    # 用于 prompt 的预读指标（自指需等生成后才能精确计算）
    history_queries = living_field.get_history_queries(session_id)
    delta_seconds = living_field.get_history_delta_seconds(session_id)
    time_factor = 1.0 - math.exp(-delta_seconds / GEOMETRY_CONSTANTS["tau_dec_seconds"])
    pre_novelty = vector_kb.novelty_score(clean_query, history_queries) if vector_kb else 0.5
    norm_eta = (eta_before - GEOMETRY_CONSTANTS["eta_background"]) / (
        GEOMETRY_CONSTANTS["eta_p2"] - GEOMETRY_CONSTANTS["eta_background"]
    )
    pre_metrics = {
        "novelty": round(pre_novelty, 6),
        "coherence": 0.0,
        "relaxation": 0.0,
        "resonance": 0.0,
        "self_reference": 0.0,
        "geo_density": 0.0,
        "time_delta_sec": int(delta_seconds),
        "time_factor": round(time_factor, 6),
        "stage_factor": round(1.0 + norm_eta, 6),
        "noise": 0.0,
    }

    # 把文件内容从 system prompt 移到 user 消息中（模型对 user 消息注意力更强）
    # system prompt 中只保留提示，不包含实际文件内容
    # 新 session 时获取最近对话标题作为轻量参考
    recent_chats_summary = ""
    if session_info['last_time'] is None and OPENWEBUI_DB_PATH and os.path.exists(OPENWEBUI_DB_PATH):
        try:
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(OPENWEBUI_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title FROM chat ORDER BY created_at DESC LIMIT 3"
            )
            recent_titles = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            if recent_titles:
                recent_chats_summary = "\n【最近对话（仅供参考，不要编造细节）】\n" + "\n".join(f"- {t}" for t in recent_titles) + "\n"
        except Exception as e:
            logger.warning(f"[RECENT_CHATS] 获取最近对话失败: {e}")

    raw_messages = data.get('messages', [])
    msg_count = len([m for m in raw_messages if isinstance(m, dict) and m.get('role') == 'user'])
    system_prompt = build_system_prompt(
        eta_before, stage, strategy, max_eta, markers,
        loaded_chunks, articles_content, pre_metrics,
        index_empty, search_no_result, "", teaching_section, msg_count, recent_chats_summary
    )

    # ============ 几何护法 · 开局注入 ============
    # 推导类问题：注入开局建议（策略推荐 + 定理导航）
    if is_derivation_query(clean_query) and results:
        try:
            article_nums = extract_article_numbers(results)
            guardian_advice = generate_opening_advice(
                query=clean_query,
                retrieved_articles=article_nums,
                vector_kb=vector_kb,
            )
            if guardian_advice:
                system_prompt = system_prompt + "\n\n" + guardian_advice
                logger.info(
                    f"[GUARDIAN] 开局建议已注入: "
                    f"类型={len(guardian_advice)}字符, "
                    f"涉及文章={len(article_nums)}篇"
                )
        except Exception as _ge:
            logger.error(f"[GUARDIAN] 开局建议生成失败，跳过: {_ge}")

    # ============ 推导工作台 · 五线并行（接入对话主流程） ============
    # 硬推导题触发五线分头推 → 结果全保留 → 横向比较找交叉印证（单线程推不出）
    # 非流式同步执行并注入推导上下文；流式后台预热（结果进缓存，供下轮/重试复用），
    # 保障首字即时；失败一律静默降级为普通回答。
    if _workbench_gate(clean_query, bool(results)):
        # 闭环：流式与非流式都同步跑五线并行 → 注入 system_prompt，保证交叉印证真进入回答。
        # 代价：硬推导请求首字需等五线完成（推导题本身需要先分头推再下结论，可接受）。
        try:
            if stream:
                logger.info("[WB-GATE] 流式硬推导：同步等五线并行完成后再流式输出（保证交叉印证闭环）")
            _wb_inject = _run_auto_workbench(clean_query, results,
                                             data.get('model') or '', system_prompt,
                                             session_id, vector_kb=vector_kb)
            if _wb_inject:
                system_prompt = system_prompt + _wb_inject
                logger.info(f"[WB-GATE] 五线并行已注入推导上下文 (len={len(_wb_inject)})")
        except Exception as _wbe:
            logger.error(f"[WB-GATE] 自动五线推导失败，降级普通回答: {_wbe}")

    # 过滤掉空消息和中间层注入的文件消息（避免历史中残留的文件内容被重复处理）
    _FILE_INJECT_MARKER = "【新文件 ·"
    raw_messages = data.get('messages', [])
    clean_messages = []
    for m in raw_messages:
        if not isinstance(m, dict):
            continue
        content = m.get('content', '')
        role = m.get('role', '')
        # 跳过中间层之前注入的文件消息
        if isinstance(content, str) and content.startswith(_FILE_INJECT_MARKER):
            continue
        # 角色兼容：developer -> system（Open WebUI 特定角色，DeepSeek 不支持）
        if role == 'developer':
            role = 'system'
            m['role'] = role
        # assistant 消息：即使 content 为空/null，如果有 tool_calls 也要保留
        if role == 'assistant' and m.get('tool_calls'):
            clean_messages.append(m)
            continue
        # assistant 消息：content 为 null 时替换为空字符串（DeepSeek 不接受 null）
        if role == 'assistant' and content is None:
            m['content'] = ""
            clean_messages.append(m)
            continue
        # tool 消息：保留（content 可能为空字符串但不应过滤）
        if role == 'tool':
            if m.get('content') is None:
                m['content'] = ""
            clean_messages.append(m)
            continue
        if isinstance(content, str) and not content.strip():
            continue
        # 处理 list 格式的 content（Open WebUI 多模态消息）
        if isinstance(content, list):
            has_text = any(
                isinstance(item, dict) and item.get('type') == 'text' and item.get('text', '').strip()
                for item in content
            )
            has_image = any(
                isinstance(item, dict) and item.get('type') == 'image_url'
                for item in content
            )
            if not has_text and not has_image:
                continue  # 空消息
            # 纯图片无文字时，保留原样（API 支持纯图片数组）
            if has_image and not has_text:
                pass  # content 数组不为空，直接保留
            m = {**m, 'content': content}
        clean_messages.append(m)

    # 如果有上传文件，在最后一条 user 消息前插入文件内容（带时间戳标记新旧）
    if files_content:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_user_msg = {
            "role": "user",
            "content": (
                f"【新文件 · {now_str}】以下是用户刚刚上传的文件，请仔细阅读并基于它回答问题。\n"
                f"注意：对话历史中可能包含之前的旧文件内容，那些已经过时，请以本条消息中的文件为准。\n\n"
                f"{files_content}"
            )
        }
        # 插入到倒数第二条位置（最后一条是用户的实际问题）
        clean_messages.insert(max(0, len(clean_messages) - 1), file_user_msg)
        # 标记这些文件为已注入（只在真正发送给模型时才标记）
        for fpath, mtime_str in ow_injected_info:
            with _injected_files_lock:
                _injected_files[fpath] = mtime_str

    final_messages = [{"role": "system", "content": system_prompt}] + clean_messages

    # 兼容性清洗：确保所有消息的 content 不为 null（DeepSeek 等严格 API 不接受 null）
    for msg in final_messages:
        if msg.get("content") is None:
            msg["content"] = ""
        # DeepSeek 兼容：补全 tool_calls 中缺少的 type 字段
        if "tool_calls" in msg and isinstance(msg["tool_calls"], list):
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict) and "type" not in tc:
                    tc["type"] = "function"
                if isinstance(tc, dict) and "function" in tc and isinstance(tc["function"], dict):
                    if "type" not in tc["function"]:
                        tc["function"]["type"] = "function"
        # DeepSeek 兼容：如果 assistant 消息有 reasoning_content 但为空，移除它
        # 如果有 reasoning_content 则保留（DeepSeek 思考模式要求回传）
        if msg.get("role") == "assistant" and "reasoning_content" in msg:
            if not msg["reasoning_content"] or not str(msg["reasoning_content"]).strip():
                del msg["reasoning_content"]

    # DeepSeek 兼容：确保 content 数组中每个元素都有 type 字段
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        if isinstance(content, list):
            for j, item in enumerate(content):
                if isinstance(item, dict) and "type" not in item:
                    # 推断 type
                    if "image_url" in item or "url" in item:
                        item["type"] = "image_url"
                    elif "text" in item:
                        item["type"] = "text"
                    else:
                        item["type"] = "text"
                    logger.warning(f"[CLEAN] 消息[{i}] content[{j}] 缺少type字段，已推断为 {item['type']}")
    # 修复多模态消息：API 要求 content 数组中每个 text 元素都不能为空
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        if isinstance(content, list):
            has_valid_text = False
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_val = item.get("text", "")
                    if not text_val or not text_val.strip():
                        # 空 text 元素，填充默认文本
                        item["text"] = "请查看这张图片并回答相关问题。"
                        logger.info(f"[FIX] 空text元素已填充 (index={i}, role={msg.get('role')})")
                    else:
                        has_valid_text = True
            if not has_valid_text:
                # 没有任何有效 text，在开头插入一个
                content.insert(0, {"type": "text", "text": "请查看这张图片并回答相关问题。"})
                logger.info(f"[FIX] 纯图片消息补充默认文本 (index={i}, role={msg.get('role')})")
            final_messages[i]["content"] = content

    # 诊断日志：打印包含图片的消息
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        if isinstance(content, list):
            types = []
            for item in content:
                if isinstance(item, dict):
                    t = item.get("type", "?")
                    if t == "text":
                        tl = len(item.get("text", ""))
                        types.append(f"text({tl})")
                    else:
                        types.append(t)
            logger.info(f"[IMG-DEBUG] index={i}, role={msg.get('role')}, types={types}")

    # 历史消息截断：保留 system + 最近 N 条消息，防止 token 爆炸
    MAX_HISTORY_MESSAGES = 80  # 最近 80 条消息（约 40 轮对话）
    MAX_HISTORY_CHARS = 120000  # 历史消息总字符上限（DeepSeek 支持 64K tokens ≈ 128K 字符）
    if len(final_messages) > MAX_HISTORY_MESSAGES + 1:  # +1 是 system
        trimmed = final_messages[1:-(MAX_HISTORY_MESSAGES)]
        # 生成本地摘要（不调 API，提取关键信息）
        summary_parts = []
        for msg in trimmed:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                preview = content[:200].replace("\n", " ")
                summary_parts.append(f"{role}: {preview}...")
            elif isinstance(content, list):
                # 多模态消息
                types = [item.get("type", "?") for item in content if isinstance(item, dict)]
                summary_parts.append(f"{role}: [{', '.join(types)}]")
        if summary_parts:
            summary_text = "【早期对话摘要（已被截断）】\n" + "\n".join(summary_parts[:20])  # 最多20条摘要
            summary_msg = {"role": "system", "content": summary_text}
            final_messages = [final_messages[0], summary_msg] + final_messages[-(MAX_HISTORY_MESSAGES):]
        else:
            final_messages = [final_messages[0]] + final_messages[-(MAX_HISTORY_MESSAGES):]
        logger.info(f"[TRIM] 历史消息从 {len(clean_messages)} 条截断到 {MAX_HISTORY_MESSAGES} 条（含摘要）")

    # 字符数超限处理（token 节省整改 2026-08-26 升级：比例制阈值，按模型窗口 × 80%）
    _req_model_hc = data.get('model') or None
    _hist_threshold = _history_threshold_chars(_req_model_hc)
    _hist_chars = sum(len(json.dumps(m, ensure_ascii=False)) for m in final_messages)
    if _hist_chars > _hist_threshold:
        final_messages = compact_history_messages(
            final_messages,
            model=_req_model_hc,
        )

    # ---- 修复 tool_calls 完整性（截断后可能导致tool_calls和tool响应不匹配）----
    # 1. assistant有tool_calls但后面缺tool响应 → 移除tool_calls
    # 2. 孤立的tool响应（没有对应assistant tool_calls）→ 移除
    _fixed = []
    for _i, _msg in enumerate(final_messages):
        if _msg.get("role") == "assistant" and _msg.get("tool_calls"):
            _tc_ids = {tc.get("id") for tc in _msg["tool_calls"] if tc.get("id")}
            _has_all = True
            for _tcid in _tc_ids:
                _found = any(
                    final_messages[_j].get("role") == "tool" and final_messages[_j].get("tool_call_id") == _tcid
                    for _j in range(_i + 1, len(final_messages))
                )
                if not _found:
                    _has_all = False
                    break
            if not _has_all:
                _msg_copy = {k: v for k, v in _msg.items() if k != "tool_calls"}
                if not _msg_copy.get("content"):
                    _msg_copy["content"] = ""
                logger.warning(f"[CLEAN] 移除不完整tool_calls（截断导致缺tool响应）")
                _fixed.append(_msg_copy)
                continue
        if _msg.get("role") == "tool":
            _tcid = _msg.get("tool_call_id")
            _has_match = False
            for _j in range(len(_fixed) - 1, -1, -1):
                _prev = _fixed[_j]
                if _prev.get("role") == "assistant" and _prev.get("tool_calls"):
                    if _tcid in {tc.get("id") for tc in _prev["tool_calls"] if tc.get("id")}:
                        _has_match = True
                        break
                if _prev.get("role") == "user":
                    break
            if not _has_match:
                logger.warning(f"[CLEAN] 移除孤立tool响应 (id={_tcid})")
                continue
        _fixed.append(_msg)
    final_messages = _fixed
    # 模型路由：全部统一使用 qwen3.7-flash
    _requested_model = data.get('model', '')
    _selected_model = GAI_MODEL
    _query_lower = clean_query.lower() if clean_query else ""
    _is_retrieval_query = any(kw in _query_lower for kw in ['哪篇文章', '哪些文章', '在哪些', '搜一搜', '哪篇', '有没有相关', '相关文章', '查编号'])
    _is_simple = (
        (len(clean_query) < 60 or _is_retrieval_query) and
        not any(kw in _query_lower for kw in ['定理', '推导', '证明', '公式', '计算', 'theta', 'lambda', '谱', '特征值', '作用量', '公理'])
        and not any(c in clean_query for c in ['∑', '∫', '∂', '∇', 'θ', 'λ'])
    )
    # 如果 Open WebUI 指定了模型，优先使用
    if _requested_model:
        _selected_model = _requested_model
        _known_models = {GAI_MODEL, GAI_MODEL_LITE, GAI_MODEL_VISION}
        _known_models.update(EXTRA_MODELS)
        _known_models_lower = {m.lower() for m in _known_models}
        if _selected_model.lower() not in _known_models_lower:
            logger.info(f"[ROUTE] 未知模型 {_selected_model}，替换为默认模型 {GAI_MODEL}")
            _selected_model = GAI_MODEL
    logger.info(f"[MODEL-ROUTE] 使用模型: {_selected_model}")

    api_params = {"model": _selected_model, "messages": final_messages}
    # ---------- 图片 / 视觉模型智能路由 ----------
    # 检测用户消息中是否包含 image_url
    _final_has_image = False
    for _msg in final_messages:
        _c = _msg.get("content")
        if isinstance(_c, list):
            for _item in _c:
                if isinstance(_item, dict) and _item.get("type") == "image_url":
                    _final_has_image = True
                    break
        if _final_has_image:
            break
    if _final_has_image:
        logger.info(f"[VISION] 检测到图片，使用前端选择的模型 {_selected_model}")
        # system prompt 中注入视觉能力提示
        _vision_note = (
            "\n\n【视觉能力已激活】你同时具有文本和图片处理能力。"
            "如果用户上传了图片，请仔细观察并理解图片内容（包括但不限于：图解、公式截图、手写笔记、图表、代码截图等），"
            "然后结合共扼谱几何知识回答问题。对于图片中的公式，尝试用 LaTeX 转写；对于手写内容，尽力辨认后给出回答。"
        )
        final_messages[0]["content"] = final_messages[0]["content"] + _vision_note
        # 检查当前模型是否支持 image_url
        _vision_supports_image = not any(p in _selected_model.lower() for p in ['deepseek', 'gemini-1.5', 'claude-3-haiku', 'claude-3-sonnet'])
        if not _vision_supports_image:
            # 模型不支持 image_url -> 移除图片元素，保留文本
            logger.warning(f'[VISION] 模型 {_selected_model} 不支持 image_url，将移除图片元素')
            for _vi_msg in final_messages:
                _c = _vi_msg.get("content")
                if isinstance(_c, list):
                    _text_parts = []
                    for _item in _c:
                        if isinstance(_item, dict) and _item.get("type") == "text":
                            _text_parts.append(_item.get("text", ""))
                        elif isinstance(_item, str):
                            _text_parts.append(_item)
                    _vi_msg["content"] = "\n".join(_text_parts)
            logger.info(f"[VISION] 已移除 image_url，保留文本，使用模型 {_selected_model}")
        else:
            logger.info(f"[VISION] 模型 {_selected_model} 支持 image_url，保持图片")
    # 仅当模型支持 function calling 时才注入工具定义
    # DeepSeek、OpenAI、Qwen、GLM 等主流模型均支持
    _model_lower = _selected_model.lower()
    _supports_tools = any(p in _model_lower for p in ['deepseek', 'gpt', 'qwen', 'glm', 'claude', 'gemini', 'chatglm', 'kimi', 'moonshot', 'doubao'])
    if _supports_tools and not _is_subagent:
        if _is_simple:
            # 简单问题（lite 模型）只注入核心工具，节省约 60% 工具定义 token
            _lite_tool_names = {
                'get_current_time', 'vector_search', 'view_article',
                'list_articles', 'personal_read', 'chat_history',
                'shell_execute', 'file_read', 'file_write', 'file_list',
                'calculate_math'
            }
            _lite_tools = [t for t in ARTICLE_TOOLS if t['function']['name'] in _lite_tool_names]
            api_params["tools"] = _lite_tools or ARTICLE_TOOLS
            logger.info(f"[ROUTE] 简单问题注入精简工具集: {len(_lite_tools)}/{len(ARTICLE_TOOLS)} 个")
        else:
            api_params["tools"] = ARTICLE_TOOLS
    else:
        logger.info(f"[ROUTE] 模型 {_selected_model} 可能不支持 function calling，跳过工具注入")
    if _final_has_image:
        logger.info(f"[VISION] 视觉模型 {_selected_model}，保留 tools 参数")

    # 思考模式兼容：DeepSeek 和 Qwen 都使用 reasoning_content
    _supports_thinking = any(p in _selected_model.lower() for p in ['deepseek', 'qwen', 'doubao'])
    if _supports_thinking:
        for msg in final_messages:
            if msg.get("role") == "assistant" and "reasoning_content" in msg:
                rc = msg.get("reasoning_content", "")
                if rc and str(rc).strip():
                    original = msg.get("content", "")
                    if original and str(original).strip():
                        msg["content"] = f"[思考过程]\n{rc}\n[/思考过程]\n\n{original}"
                    else:
                        msg["content"] = f"[思考过程]\n{rc}\n[/思考过程]"
                del msg["reasoning_content"]
    else:
        # 非思考模式模型：直接删除 reasoning_content 字段
        for msg in final_messages:
            if "reasoning_content" in msg:
                del msg["reasoning_content"]

    # 诊断：打印每条消息的结构（用于排查 DeepSeek 格式问题）
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        content_desc = f"str({len(str(content))})" if isinstance(content, str) else f"list({len(content)})" if isinstance(content, list) else str(content)[:50]
        keys = list(msg.keys())
        logger.info(f"[MSG-DEBUG] [{i}] keys={keys}, content={content_desc}, role={msg.get('role')}")
        # 如果 content 是数组，打印每个元素的 keys
        if isinstance(content, list):
            for j, item in enumerate(content):
                if isinstance(item, dict):
                    logger.info(f"[MSG-DEBUG]   [{i}][{j}] keys={list(item.keys())}, type={item.get('type', 'MISSING')}")
    # 中间层使用自有工具定义（ARTICLE_TOOLS），不透传 Open WebUI 的 tools 参数
    # 原因：中间层代理模式下，工具调用在中间层内部完成，Open WebUI 不需要感知
    # 透传 Open WebUI 的标准参数
    # 默认启用深度思考
    _model_lower_check = _selected_model.lower() if '_selected_model' in dir() else os.getenv('GAI_MODEL', '').lower()
    _is_deepseek_model = 'deepseek' in _model_lower_check
    _is_qwen_model = 'qwen' in _model_lower_check
    _is_doubao_model = 'doubao' in _model_lower_check
    if _is_deepseek_model:
        if 'reasoning_effort' not in data:
            api_params['reasoning_effort'] = 'high'
        elif data['reasoning_effort']:
            api_params['reasoning_effort'] = data['reasoning_effort']
    elif _is_qwen_model:
        # Qwen 思考模式：通过 extra_body 启用 enable_thinking
        api_params['extra_body'] = {'enable_thinking': True}
    elif _is_doubao_model:
        # Doubao 2.1 思考模式：通过 extra_body 启用 thinking
        api_params['extra_body'] = {'thinking': {'type': 'enabled'}}
    for key in ('temperature', 'max_tokens', 'top_p', 'stop', 'frequency_penalty', 'presence_penalty', 'tool_choice', 'stream_options', 'response_format', 'user'):
        if key in data:
            api_params[key] = data[key]
    # tool_choice 仅在注入了工具时才透传
    if 'tools' not in api_params and 'tool_choice' in api_params:
        del api_params['tool_choice']
        logger.info("[ROUTE] 未注入工具，移除 tool_choice 参数")
    # max_tokens 上限保护（不同模型限制不同）
    if 'max_tokens' in api_params:
        _max_limit = 16384  # 保守上限，大多数模型都支持
        if api_params['max_tokens'] > _max_limit:
            logger.warning(f"[ROUTE] max_tokens {api_params['max_tokens']} 超过上限 {_max_limit}，已限制")
            api_params['max_tokens'] = _max_limit

    if stream:
        def gen():
            try:
                collected = []
                _ctx_usage = None
                _ctx_finish_reason = "stop"
                for ev in stream_generate(data, eta_before, final_messages, api_params, vector_kb=vector_kb):
                    yield ev
                    try:
                        if ev.startswith('data: '):
                            payload = ev[6:].strip()
                            if payload and payload != '[DONE]':
                                d = json.loads(payload)
                                c = d['choices'][0]['delta'].get('content', '')
                                if c:
                                    collected.append(c)
                                if 'usage' in d and d['usage']:
                                    _ctx_usage = d['usage']
                                fr = d['choices'][0].get('finish_reason') if d.get('choices') else None
                                if fr:
                                    _ctx_finish_reason = fr
                    except Exception as e:
                        logger.debug(f"[SSE] chunk JSON解析失败: {e}")
                response_text = ''.join(collected)
                # 在后台线程执行 finalize，不阻塞 SSE 响应
                import threading
                _ctx = (session_id, clean_query, response_text, eta_before, articles_content, loaded_chunks, _ctx_usage, _selected_model, _ctx_finish_reason)
                threading.Thread(target=_finalize_turn, args=_ctx, daemon=True).start()
            except Exception as e:
                logger.error(f"[CHAT-STREAM] 生成器异常: {e}")
                err = {"error": {"message": str(e), "type": "server_error", "param": None, "code": None}}
                yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        return Response(
            gen(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache, no-transform',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )
    else:
        # 非流式：使用已路由的 _selected_model 确定提供商
        base_url, api_key = get_provider_for_model(_selected_model)
        # 禁代理直连（避免 sandbox 注入的 http_proxy=127.0.0.1:7897 导致可连接失败的场景）
        _no_proxy_client = _httpx.Client(trust_env=False)
        client = openai.OpenAI(api_key=api_key, base_url=base_url, http_client=_no_proxy_client, timeout=180.0, max_retries=1)
        try:
            # 质量门控 - 如果AI回复偏离共扼谱几何，自动重试
            # v10 增强：反模式检测触发重试时，在prompt中注入反模式警告
            # 工具调用链（非流式）——处理 KIMI 等模型的 function calling
            MAX_TOOL_CHAIN = 15
            for _tc_round in range(MAX_TOOL_CHAIN):
                resp = client.chat.completions.create(**api_params)
                _tc_content = resp.choices[0].message.content or ""
                # 检查是否有 tool_calls
                if (not _tc_content or _tc_content == "") and hasattr(resp.choices[0].message, "tool_calls") and resp.choices[0].message.tool_calls:
                    _tcs = resp.choices[0].message.tool_calls
                    logger.info(f"[TOOL] 工具调用 #{_tc_round+1}: {len(_tcs)} 个")
                    # 追加 assistant 消息含 tool_calls
                    _asst = {"role": "assistant", "content": None, "tool_calls": []}
                    for _tc in _tcs:
                        _asst["tool_calls"].append({"id": _tc.id, "type": "function", "function": {"name": _tc.function.name, "arguments": _tc.function.arguments}})
                    clean_messages.append(_asst)
                    # 执行并追加工具结果
                    for _tc in _tcs:
                        try:
                            _args = json.loads(_tc.function.arguments)
                        except Exception:
                            _args = {}
                        _result = execute_tool_call(_tc.function.name, _args, vector_kb=vector_kb, session_id=session_id)
                        _result_str = str(_result)
                        # 单个工具结果超长修剪（与 stream.py 一致：dsh pruner 风格，保头尾+中间标记）
                        if len(_result_str) > 8192:
                            _rlen = len(_result_str)
                            _result_str = (_result_str[:3000]
                                           + f"\n\n[... 工具结果中部已修剪，原始长度 {_rlen} 字符。如需中间内容请用 offset/limit 或 section 精确读取 ...]\n\n"
                                           + _result_str[-2000:])
                            logger.info(f"[TOOL] 非流式工具结果超长，头/尾修剪至 3000+2000 (原始 {_rlen} 字符)")
                        clean_messages.append({"role": "tool", "tool_call_id": _tc.id, "content": _result_str})
                    # 更新 messages 重新请求
                    api_params["messages"] = [{"role": "system", "content": system_prompt}] + clean_messages
                else:
                    # 正常回复，使用这个 response_text
                    response_text = _tc_content
                    break
            response_text = ""
            _bad_cite_hint_prev = ""
            for attempt in range(1 + MAX_QUALITY_RETRIES):
                if attempt > 0:
                    logger.info(f"[QUALITY-GATE] 第{attempt+1}次重试（检测到低质量回复）")
                    retry_prompt = system_prompt + "\n\n【紧急指令 - 上次回复质量不合格】\n你必须基于共扼谱几何框架给出实质性回答。禁止说'未找到引用'、'无法访问'、'我是AI'等偏离共扼谱几何的话。直接用公理、定理、命题来回答。"
                    # 引用硬校验失败时，把具体不存在编号注入重试提示
                    if _bad_cite_hint_prev:
                        retry_prompt += _bad_cite_hint_prev

                    # v10 新增：如果是因为反模式触发，额外注入反模式警告
                    if teaching_system:
                        try:
                            is_triggered, triggered = teaching_system.check_antipattern_triggered(response_text)
                            if is_triggered:
                                high_pats = [t for t in triggered if t['severity'] == 'high']
                                for hp in high_pats:
                                    retry_prompt += f"\n【反模式触发】你的回复包含了被禁止的模式：'{hp['pattern']}'，请避免。"
                        except Exception as e:
                            logger.error(f"[QUALITY-GATE] 反模式检测失败: {e}")

                    api_params_retry = dict(api_params)
                    api_params_retry["messages"] = [{"role": "system", "content": retry_prompt}] + clean_messages
                    resp = client.chat.completions.create(**api_params_retry)
                else:
                    resp = client.chat.completions.create(**api_params)
                response_text = resp.choices[0].message.content or ""

                # 提取 usage 信息
                _usage = None
                if hasattr(resp, 'usage') and resp.usage:
                    _usage = {
                        "prompt_tokens": resp.usage.prompt_tokens or 0,
                        "completion_tokens": resp.usage.completion_tokens or 0,
                        "total_tokens": resp.usage.total_tokens or 0,
                        "prompt_cache_hit_tokens": getattr(resp.usage, 'prompt_cache_hit_tokens', 0) or 0,
                        "prompt_cache_miss_tokens": getattr(resp.usage, 'prompt_cache_miss_tokens', 0) or 0
                    }

                if not QUALITY_GATE_ENABLED:
                    break

                # 跳过不需要质量门控的请求
                _skip_quality = False
                # Open WebUI 系统请求（标题/标签生成等）
                if clean_query.startswith("### Task:") or clean_query.startswith("Generate"):
                    _skip_quality = True
                # 非共扼谱几何问题（短查询、无专业术语）
                elif len(clean_query) < 20:
                    _skip_quality = True
                # 闲聊/日常对话
                elif any(kw in clean_query for kw in ['你好', '谢谢', '再见', 'hello', 'thanks', 'bye']):
                    _skip_quality = True
                if _skip_quality:
                    break

                # v10 增强：传入 teaching_system 进行反模式检测
                is_good, reason = check_response_quality(response_text, teaching_system=teaching_system)
                # 引用来源硬校验：检查还原引用不存在的文章编号
                _cite = None
                if is_good:
                    try:
                        _cite = verify_citations(response_text, _REAL_ARTICLE_IDS)
                        if not _cite["ok"]:
                            is_good = False
                            reason = f"幻觉引用: 引用了不存在的文章编号 {[b[0] for b in _cite['bad']]}"
                            logger.warning(f"[CITE-GATE] {reason}")
                    except Exception as e:
                        logger.error(f"[CITE-GATE] 引用校验失败: {e}")
                if is_good:
                    break
                else:
                    logger.warning(f"[QUALITY-GATE] 回复质量不合格: {reason}")
                    # 引用校验失败时，把具体幻觉编号注入重试提示，引导模型修正
                    try:
                        if _cite and not _cite["ok"]:
                            _bad_cite_hint_prev = "\n\n【引用硬校验失败】" + format_bad_citations(_cite["bad"])
                    except Exception as e:
                        logger.error(f"[CITE-GATE] 重写提示生成失败: {e}")
                    if attempt == MAX_QUALITY_RETRIES:
                        logger.warning(f"[QUALITY-GATE] 已达最大重试次数，使用最后一次回复")
        except Exception as e:
            logger.error(f"[CHAT] 生成错误: {e}")
            return openai_error(str(e), status=502)
        # token 节省整改：请求结束清理会话级工具状态（calculate_math 命名空间等）
        try:
            reset_tool_session(session_id)
        except Exception:
            pass
        result = _finalize_turn(session_id, clean_query, response_text, eta_before, articles_content, loaded_chunks, usage=_usage, request_model=_selected_model, finish_reason=getattr(resp.choices[0], 'finish_reason', None) or "stop")
        return jsonify(result)


# ==================== Responses API 兼容层 (Codex++/新版客户端 wire_api=responses) ====================
def _responses_input_to_messages(src) -> List[Dict[str, Any]]:
    """把 Responses API 的 input/instructions 翻译成 chat messages"""
    msgs: List[Dict[str, Any]] = []
    if isinstance(src, str):
        if src.strip():
            msgs.append({"role": "user", "content": src})
    elif isinstance(src, list):
        for item in src:
            if isinstance(item, str):
                if item.strip():
                    msgs.append({"role": "user", "content": item})
            elif isinstance(item, dict):
                # {role, content} 或 {type:message, role, content}
                role = item.get('role', 'user')
                content = item.get('content', '')
                if isinstance(content, list):
                    texts = [c.get('text', '') for c in content if isinstance(c, dict) and c.get('type') in ('input_text', 'text', 'output_text')]
                    content = "\n".join(t for t in texts if t)
                if isinstance(content, str) and content.strip():
                    msgs.append({"role": role, "content": content})
    return msgs


def _chat_resp_to_responses(chat_body: dict, req_model: str) -> dict:
    """把 chat.completion JSON 翻译成 Responses API JSON (非流式)"""
    choice = (chat_body.get('choices') or [{}])[0]
    text = (choice.get('message') or {}).get('content', '') or ''
    finish = choice.get('finish_reason', 'stop')
    usage = chat_body.get('usage') or {}
    created = chat_body.get('created', int(time.time()))
    resp_id = f"resp_{uuid.uuid4().hex[:24]}"
    return {
        "id": resp_id,
        "object": "response",
        "created_at": created,
        "status": "completed",
        "model": req_model,
        "output": [{
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "status": "completed",
            "role": "assistant",
            "content": [{
                "type": "output_text",
                "text": text,
                "annotations": []
            }]
        }],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "usage": {
            "input_tokens": usage.get('prompt_tokens', 0),
            "output_tokens": usage.get('completion_tokens', 0),
            "total_tokens": usage.get('total_tokens', 0),
            "prompt_cache_hit_tokens": usage.get('prompt_cache_hit_tokens', 0),
            "prompt_cache_miss_tokens": usage.get('prompt_cache_miss_tokens', 0)
        },
        "error": None,
        "finish_reason": finish,
    }


def _loop_back_chat(chat_payload: dict, auth_header: str = '', timeout: float = 300.0):
    """内部回环调用本服务 /v1/chat/completions，复用全部中间层逻辑"""
    import os as _os
    _port = _os.getenv('PORT', '5000')
    url = f"http://127.0.0.1:{_port}/v1/chat/completions"
    _headers = {'Content-Type': 'application/json'}
    if auth_header:
        _headers['Authorization'] = auth_header
    with _httpx.Client(trust_env=False, timeout=timeout) as _c:
        return _c.post(url, headers=_headers, json=chat_payload)

def _loop_back_chat_stream(chat_payload: dict, auth_header: str = '', timeout: float = 600.0):
    """流式回环：逐行 yield SSE 数据，避免工具链执行期间客户端 idle timeout"""
    import os as _os
    _port = _os.getenv('PORT', '5000')
    url = f"http://127.0.0.1:{_port}/v1/chat/completions"
    _headers = {'Content-Type': 'application/json'}
    if auth_header:
        _headers['Authorization'] = auth_header
    _c = _httpx.Client(trust_env=False, timeout=timeout)
    try:
        with _c.stream('POST', url, headers=_headers, json=chat_payload) as _resp:
            if _resp.status_code != 200:
                _body = _resp.read()
                yield ('__error__', _resp.status_code, _body)
                return
            for line in _resp.iter_lines():
                yield line
    finally:
        _c.close()


@app.route('/v1/responses', methods=['POST'])
def responses_completions():
    """Codex++ 等新版客户端 wire_api=responses 的兼容端点"""
    _auth = request.headers.get('Authorization', '')
    _api_keys = os.getenv('GAI_API_KEYS', '')
    if _api_keys:
        _allowed_keys = [k.strip() for k in _api_keys.split(',') if k.strip()]
        _provided_key = _auth.replace('Bearer ', '').strip() if _auth.startswith('Bearer ') else ''
        if _provided_key and _allowed_keys and _provided_key not in _allowed_keys:
            return openai_error("Invalid API key", "invalid_request_error", 401)

    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return openai_error("Invalid request body", err_type="invalid_request_error", status=400)

    req_model = data.get('model') or GAI_MODEL
    # 未知模型拦截：Codex++ 内部任务（标题生成等）可能发送未配置的模型（如 gpt-5.6-luna），
    # 标记后走自动路由，避免路由到不支持该模型的提供商
    _known_models = {GAI_MODEL, GAI_MODEL_LITE, GAI_MODEL_VISION}
    _known_models.update(EXTRA_MODELS)
    _known_models_lower = {m.lower() for m in _known_models}
    _model_was_unknown = False
    if req_model.lower() not in _known_models_lower:
        logger.info(f"[RESPONSES] 未知模型 {req_model}，将进行自动路由")
        _model_was_unknown = True
    stream = data.get('stream', False)
    # 缓存 auth header，供流式生成器(线程外)使用 request context 无法访问
    _auth_header = _auth

    # 组装 chat messages：instructions 作为 system，input 作为对话
    messages: List[Dict[str, Any]] = []
    _inst = data.get('instructions')
    if isinstance(_inst, str) and _inst.strip():
        messages.append({"role": "system", "content": _inst})
    messages.extend(_responses_input_to_messages(data.get('input')))
    if not messages:
        messages.append({"role": "user", "content": "请继续"})

    # token 节省整改：responses 入口同样做渐进历史压缩（Codex++ 主路径，比例制阈值）
    try:
        _r_model_hc = data.get('model') or None
        _r_threshold = _history_threshold_chars(_r_model_hc)
        _r_hist_chars = sum(len(json.dumps(m, ensure_ascii=False)) for m in messages)
        if _r_hist_chars > _r_threshold:
            messages = compact_history_messages(
                messages,
                model=_r_model_hc,
            )
    except Exception as _ce:
        logger.warning(f"[HISTORY-COMPACT] responses 压缩异常，跳过: {_ce}")

    # 统一使用 qwen3.7-flash（全部请求类型）
    _is_codex_internal = False
    _inst_str = data.get('instructions', '') or ''
    if isinstance(_inst_str, str) and 'provide a short title' in _inst_str.lower():
        _is_codex_internal = True
    if not data.get('model') or _model_was_unknown or (req_model != GAI_MODEL and not _is_codex_internal):
        req_model = GAI_MODEL
        logger.info(f"[MODEL-ROUTE] /responses 使用模型: {GAI_MODEL}")
    elif _model_was_unknown:
        req_model = GAI_MODEL
        logger.info(f"[MODEL-ROUTE] /responses 未知模型替换为: {GAI_MODEL}")

    # 透传工具与参数
    chat_payload: Dict[str, Any] = {
        "model": req_model,
        "messages": messages,
        "stream": stream,
    }
    if data.get('max_output_tokens'):
        chat_payload['max_tokens'] = data['max_output_tokens']
    if data.get('temperature') is not None:
        chat_payload['temperature'] = data['temperature']
    if data.get('top_p') is not None:
        chat_payload['top_p'] = data['top_p']
    if data.get('reasoning'):
        r = data['reasoning']
        if isinstance(r, dict) and r.get('effort'):
            chat_payload['reasoning_effort'] = r['effort']
    if data.get('tools'):
        chat_payload['tools'] = data['tools']
    if data.get('tool_choice'):
        chat_payload['tool_choice'] = data['tool_choice']
    if data.get('session_id'):
        chat_payload['session_id'] = data['session_id']

    if not stream:
        # 非流式：内部回环调用，拿 chat JSON，转 responses JSON
        try:
            _resp = _loop_back_chat(chat_payload, auth_header=_auth_header)
            if _resp.status_code != 200:
                try:
                    _err = _resp.json()
                except Exception:
                    _err = {"error": {"message": _resp.text[:500], "type": "server_error"}}
                return jsonify(_err), _resp.status_code
            _body = _resp.json()
            return jsonify(_chat_resp_to_responses(_body, req_model))
        except Exception as e:
            logger.error(f"[RESPONSES] 非流式生成错误: {e}")
            return openai_error(str(e), status=502)

    # 流式：回环到 chat 流，逐事件翻译为 Responses SSE
    def _gen():
        # 预先生成创建事件
        created = int(time.time())
        resp_id = f"resp_{uuid.uuid4().hex[:24]}"
        msg_id = f"msg_{uuid.uuid4().hex[:24]}"
        _send = lambda ev, payload: f"event: {ev}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        yield _send("response.created", {
            "type": "response.created",
            "response": {"id": resp_id, "object": "response", "created_at": created,
                         "status": "in_progress", "model": req_model, "output": [],
                         "error": None},
        })
        yield _send("response.output_item.added", {
            "type": "response.output_item.added", "output_index": 0,
            "item": {"id": msg_id, "type": "message", "status": "in_progress",
                     "role": "assistant", "content": []},
        })
        yield _send("response.content_part.added", {
            "type": "response.content_part.added", "item_id": msg_id, "output_index": 0,
            "content_index": 0, "part": {"type": "output_text", "text": "", "annotations": []},
        })

        collected = []
        _resp_usage = None
        import queue as _queue
        import threading as _threading

        _q = _queue.Queue()
        _upstream_done = False

        def _upstream_worker():
            nonlocal _upstream_done
            try:
                _up = _loop_back_chat_stream(chat_payload, auth_header=_auth_header)
                for _line in _up:
                    _q.put(('data', _line))
            except Exception as e:
                _q.put(('error', e))
            finally:
                _upstream_done = True
                _q.put(('done', None))

        _threading.Thread(target=_upstream_worker, daemon=True).start()

        try:
            while True:
                try:
                    _item = _q.get(timeout=5)
                except _queue.Empty:
                    yield ": keepalive\n\n"
                    continue

                _tag, _val = _item
                if _tag == 'done':
                    break
                if _tag == 'error':
                    logger.error(f"[RESPONSES] 流式生成错误: {_val}")
                    yield _send("response.failed", {"type": "response.failed", "response": {"error": {"type": "server_error", "message": str(_val)}}})
                    yield "data: [DONE]\n\n"
                    return
                line = _val
                if not line:
                    continue
                if line.startswith(':'):
                    continue
                if not line.startswith('data:'):
                    continue
                payload = line[5:].strip()
                if not payload or payload == '[DONE]':
                    continue
                try:
                    chunk = json.loads(payload)
                except Exception:
                    continue
                choice = (chunk.get('choices') or [{}])[0]
                delta = choice.get('delta') or {}
                _txt = delta.get('content') or ''
                if _txt:
                    collected.append(_txt)
                    yield _send("response.output_text.delta", {
                        "type": "response.output_text.delta", "item_id": msg_id,
                        "output_index": 0, "content_index": 0, "delta": _txt,
                    })
                if 'usage' in chunk and chunk['usage']:
                    _resp_usage = chunk['usage']
        except Exception as e:
            logger.error(f"[RESPONSES] 流式生成错误: {e}")
            yield _send("response.failed", {"type": "response.failed", "response": {"error": {"type": "server_error", "message": str(e)}}})
            yield "data: [DONE]\n\n"
            return

        full_text = ''.join(collected)
        yield _send("response.output_text.done", {
            "type": "response.output_text.done", "item_id": msg_id, "output_index": 0,
            "content_index": 0, "text": full_text,
        })
        yield _send("response.content_part.done", {
            "type": "response.content_part.done", "item_id": msg_id, "output_index": 0,
            "content_index": 0, "part": {"type": "output_text", "text": full_text, "annotations": []},
        })
        yield _send("response.output_item.done", {
            "type": "response.output_item.done", "output_index": 0,
            "item": {"id": msg_id, "type": "message", "status": "completed",
                     "role": "assistant", "content": [{"type": "output_text", "text": full_text, "annotations": []}]},
        })
        _final_usage = {"input_tokens": 0, "output_tokens": len(full_text), "total_tokens": len(full_text)}
        if _resp_usage:
            _pt = _resp_usage.get('prompt_tokens', 0)
            _ct = _resp_usage.get('completion_tokens', 0)
            _ch = _resp_usage.get('prompt_cache_hit_tokens', 0)
            _cm = _resp_usage.get('prompt_cache_miss_tokens', 0)
            _final_usage = {
                "input_tokens": _pt,
                "output_tokens": _ct,
                "total_tokens": _pt + _ct,
                "prompt_cache_hit_tokens": _ch,
                "prompt_cache_miss_tokens": _cm,
            }
            if _pt > 0:
                logger.info(f"[CACHE] prompt={_pt} hit={_ch} miss={_cm} rate={_ch/_pt*100:.1f}% model={req_model}")

        yield _send("response.completed", {
            "type": "response.completed",
            "response": {"id": resp_id, "object": "response",
                         "created_at": created, "status": "completed", "model": req_model,
                         "output": [{"id": msg_id, "type": "message", "status": "completed",
                                     "role": "assistant", "content": [{"type": "output_text", "text": full_text, "annotations": []}]}],
                         "error": None,
                         "usage": _final_usage},
        })
        yield "data: [DONE]\n\n"

    return Response(
        _gen(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'},
    )


# ==================== 启动 ====================

def init_server():
    global living_field, vector_kb, teaching_system

    _refresh_real_article_ids()

    living_field = LivingInfoField()

    vector_kb = VectorKnowledgeBase(CHROMA_DB_DIR)
    if vector_kb.initialize():
        try:
            _mem = vector_kb.preload_all(UPLOAD_FOLDER)
            logger.info(f"[STARTUP] 全内存模式: {_mem['articles_in_memory']} 篇文章全文已载入 "
                        f"({_mem['mb']} MB) | chunks={_mem['chunks']} | "
                        f"摘要图={_mem['summary_map']} 引用边={_mem['graph_edges']}")
        except Exception as _e:
            logger.warning(f"[STARTUP] 全内存预热失败: {_e}")
        logger.info(f"[STARTUP] DEBUG: articles_count={vector_kb.articles_count}, UPLOAD_FOLDER={UPLOAD_FOLDER}, exists={os.path.exists(UPLOAD_FOLDER)}")
        if vector_kb.articles_count == 0:
            diag = vector_kb.build_index(UPLOAD_FOLDER)
            if vector_kb.articles_count > 0:
                logger.info(f"[STARTUP] 向量索引构建成功: {vector_kb.articles_count} 个文本块")
            else:
                logger.warning(f"[STARTUP] 向量索引构建失败: {diag.get('errors', [])}")
        else:
            logger.info(f"[STARTUP] 已有向量索引: {vector_kb.articles_count} 个文本块")
    else:
        logger.warning("[STARTUP] ChromaDB 初始化失败，向量检索不可用")

    if vector_kb and vector_kb.is_initialized:
        teaching_system = TeachingSystem(vector_kb)
    else:
        logger.warning("[STARTUP] 教学系统初始化失败（向量库不可用）")

    logger.info(f"[STARTUP] ===== 共扼谱几何AI {VERSION} (build {BUILD_DATE}) =====")
    logger.info(f"[STARTUP] 文章目录: {UPLOAD_FOLDER}")
    logger.info(f"[STARTUP] ChromaDB 目录: {CHROMA_DB_DIR}")
    logger.info(f"[STARTUP] ChromaDB 状态: {'已连接' if vector_kb and vector_kb.is_initialized else '未连接'}")
    if vector_kb and vector_kb.is_initialized:
        logger.info(f"[STARTUP] 向量库 articles: {vector_kb.articles_count} | learned: {vector_kb.learned_count}")
        logger.info(f"[STARTUP] 教学集合 corrections: {vector_kb.corrections_count} | antipatterns: {vector_kb.antipatterns_count} | patches: {vector_kb.patches_count}")
    logger.info("[STARTUP] 数据库模式: 内存（无MySQL依赖），eta 由活体信息场管理")
    logger.info(f"[STARTUP] Open WebUI uploads: {OPENWEBUI_UPLOAD_DIR} (存在: {os.path.exists(OPENWEBUI_UPLOAD_DIR)})")
    logger.info(f"[STARTUP] 质量门控: {'开启' if QUALITY_GATE_ENABLED else '关闭'}, 最大重试: {MAX_QUALITY_RETRIES}")
    logger.info(f"[STARTUP] 学习闭环: coherence > {LEARN_COHERENCE_THRESHOLD}, 长度 > {LEARN_MIN_LENGTH}")
    logger.info(f"[STARTUP] 自指反馈环: 已启用（回复共扼谱几何术语密度 -> eta 自指增强 + 论断提取）")
    if teaching_system:
        stats = teaching_system.get_stats()
        logger.info(
            f"[STARTUP] 教学系统状态: "
            f"纠正={stats['corrections_count']} | "
            f"反模式={stats['antipatterns_count']} | "
            f"知识补丁={stats['patches_count']}"
        )
    else:
        logger.info("[STARTUP] 教学系统: 未初始化")
    if os.path.exists(OPENWEBUI_UPLOAD_DIR):
        try:
            cnt = len([f for f in os.listdir(OPENWEBUI_UPLOAD_DIR) if os.path.isfile(os.path.join(OPENWEBUI_UPLOAD_DIR, f))])
            logger.info(f"[STARTUP] Open WebUI uploads 目录中有 {cnt} 个文件")
        except Exception as e:
            logger.debug(f"[STARTUP] 列出上传目录失败: {e}")

    import tools as _tools_mod
    _tools_mod.vector_kb = vector_kb
    _tools_mod.teaching_system = teaching_system
    _tools_mod.living_field = living_field

    import subprocess as _sp
    _port = 5000
    try:
        _current_pid = os.getpid()
        _port_pids = _sp.check_output(['lsof', '-ti', f':{_port}'], stderr=_sp.DEVNULL).decode().strip().split('\n')
        for _pid_str in _port_pids:
            _pid_str = _pid_str.strip()
            if _pid_str and int(_pid_str) != _current_pid:
                logger.warning(f"[STARTUP] 端口 {_port} 被占用，正在清理旧进程 PID={_pid_str}...")
                try:
                    os.kill(int(_pid_str), 9)
                    time.sleep(2)
                except ProcessLookupError:
                    pass
    except (_sp.CalledProcessError, FileNotFoundError, ProcessLookupError, ValueError):
        pass

    try:
        _n_wb = _WorkbenchRegistry.instance().load_all()
        _n_ss = _SessionStore.instance().load_all()
        logger.info(f"[STARTUP] 工作台常驻服务: {_n_wb} 个工作台已载入内存 "
                    f"| 内存占用 {_WorkbenchRegistry.instance().memory_stats()}")
        logger.info(f"[STARTUP] 推导会话暂存区: {_n_ss} 个会话快照已载入内存 "
                    f"| 内存占用 {_SessionStore.instance().memory_stats()}")
    except Exception as _e:
        logger.warning(f"[STARTUP] 工作台载入失败: {_e}")

    from child_judge_worker import start_worker as _start_cj_worker
    try:
        _cj_t = _start_cj_worker(_run_child_judgement_llm)
        if _cj_t is not None:
            logger.info(f"[STARTUP] 子AI自动圆满判定 worker 已启动 "
                        f"(dry_run={os.environ.get('CHILD_AUTO_JUDGE_REAL', '0') != '1'})")
    except Exception as _cj_e:
        logger.error(f"[STARTUP] 子AI自动圆满判定 worker 启动失败: {_cj_e}")


if __name__ == '__main__':
    init_server()
    app.run(host='0.0.0.0', port=5000, debug=False)
