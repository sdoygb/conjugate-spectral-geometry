#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM 驱动的五线并行推导（接入对话主流程用）。

与 derive.py（手动输入 python 验证器）不同，本模块的"五条线"各自由 LLM
从独立的推导角度蠕动式推导：每条线一套工具链（calculate_math / view_article /
vector_search），各自产出一个清晰的线结论；五个结论全部保留存档，然后横向比较，
找出 ≥2 条线独立收敛到同一结论的"交叉印证区"（这正是单线程推不出的部分），
同时保留死胡同（排除性证据），最后判定收敛并持久化到工作台磁盘。

用法（依赖注入，避免与 server.py 循环 import）：
    summary = run_llm_five_line(
        gap_id, title, anchors, target,
        base_system_prompt, client, model, tools, execute_tool,
        max_tool_chain=6, logger=logger)
"""
from __future__ import annotations
import json
import re
import uuid
from datetime import datetime
from typing import Callable, Dict, List, Optional

from .workbench import Workbench
from .derive import DerivationFlow
from .service import WorkbenchRegistry
from .templates import DERIVATION_LINES
from .models import (
    EV_VERIFIED, EV_FAILED, EV_OUTSCOPE,
    LINE_CLOSED, LINE_DEAD, LINE_PARTIAL, LINE_OPEN,
)

# 每线推导的"纪律"：强制精确计算 + 真实引用 + 多跳查定理 + 明确表态
_LINE_DISCIPLINE = (
    "\n\n【本线推导纪律】\n"
    "你现在是五线并行推导中的单独一条推导线，只从本线角度推导目标。\n"
    "- 一切数值计算、方程求解、化简、微分/积分都必须调用 calculate_math 工具得到精确结果，严禁心算。\n"
    "- 引用定理/公式必须真实存在（用 view_article 核对），不得编造编号。\n"
    "- 先沿引用链条一层一层查相关定理，再下结论，不要查到一层就宣称'无法推导'。\n"
    "- 若本角度确实打不通，请明确说'此为死胡同'并说明卡在哪一步。\n"
    "- 最后一行必须单独输出结论标记：`【线结论】<一句话结论>` 或 `【死胡同】<卡点原因>`。"
)

_DEAD_PAT = re.compile(r"【死胡同】|无法推导|无法得出|不能导出|无法确定|不可导出|推导不下去|此路不通|打不通")
_FINDING_PAT = re.compile(r"[αθκΛ]==?\s*([\d.]+)°?|[αθκΛ]≈\s*([\d.]+)|\d+\.\d+°")
_CLUSTER_NOISE = {"的", "是", "了", "在", "与", "并且", "以及", "这个", "即", "则", "因此"}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize(s: str) -> str:
    return "".join(ch for ch in s if not ch.isspace())


def _numb_claims(text: str) -> List[str]:
    """抽取文本里的数值结论（角度/谱参数类），用于跨线聚类。"""
    out = []
    for m in _FINDING_PAT.finditer(text):
        val = next((g for g in m.groups() if g), "")
        out.append(f"{m.group(0)}_{val}")
    return out[:6]


def _tokenize(s: str) -> set:
    toks = re.findall(r"[一-鿿]{2,}", s)
    return {t for t in toks if t not in _CLUSTER_NOISE}


def _symbol_claims(s: str) -> set:
    """抽取结论里的关键几何符号（θ/α/κ/Λ 及其组合），作硬碰撞信号。"""
    out = set()
    for m in re.finditer(r"([αθκλΛσμ])\s*[\u4e00-\u9fff]{0,2}?(?=\s*[=≈|])|([αθκλΛσμ])\s*[=≈]", s, re.I):
        sym = (m.group(1) or m.group(2) or "").lower()
        if sym:
            out.add(sym)
    for sym in re.findall(r"[αθκλΛσμ]", s):
        out.add(sym)
    return out


def _cosine(a, b) -> float:
    """计算两个等长向量的余弦相似度。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    import math
    def _norm(v):
        return math.sqrt(sum(x * x for x in v)) or 1e-12
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (_norm(a) * _norm(b))


def _maybe_compact_line_history(messages: List[dict], threshold_chars: int = 30000,
                                keep_recent: int = 2) -> List[dict]:
    """
    C 类上下文压缩：单线工具链 messages 累积超过阈值时，把最早的工具轮次
    浓缩成一条要点占位，仅保留最近 keep_recent 轮完整历史。
    - 被删除轮次的 tool_call_id 早已被模型消费，后续生成不会引用 → API 安全。
    - 压缩内容 = 各被删轮次 tool 结果首行 + assistant 文本首行，给模型保留"算过哪些关键值"的线索。
    - 阈值默认较高，普通短推导不触发，零行为改变；仅超长工具链生效。
    返回新的 messages 列表。
    """
    def _mchars(m: dict) -> int:
        s = str(m.get("content") or "")
        tc = m.get("tool_calls") or ""
        return len(s) + len(str(tc))

    total = sum(_mchars(m) for m in messages)
    if total <= threshold_chars:
        return messages
    # 定位所有携带 tool_calls 的 assistant 消息（每个工具往返轮次的起点）
    asst_tc_idx = [i for i, m in enumerate(messages)
                   if m.get("role") == "assistant" and m.get("tool_calls")]
    if len(asst_tc_idx) <= keep_recent:
        return messages
    cut = asst_tc_idx[-keep_recent]  # 保留区起点（该轮及之后的完整历史）

    base: List[dict] = []
    parts: List[str] = []
    read_manifest: List[str] = []  # token 节省整改：已读文章清单（防压缩后重复读）
    sys_compacted = False          # token 节省整改：system 参考资料块已骨架化
    i = 0
    while i < cut:
        m = messages[i]
        r = m.get("role")
        if r in ("system", "user"):
            # token 节省整改：system 的【参考资料】注入块骨架化（保留身份指令，压缩文章正文）
            _c = str(m.get("content") or "")
            if r == "system" and not sys_compacted and "【参考资料" in _c:
                _head, _, _tail = _c.partition("【参考资料")
                _ref_block = _tail.split("【当前状态】")[0] if "【当前状态】" in _tail else _tail[:20000]
                _ref_lines = [ln.strip() for ln in _ref_block.splitlines()
                              if ln.strip() and len(ln.strip()) > 5][:40]
                _ref_titles = [ln[:100] for ln in _ref_lines[:25]]
                _sys_c = _head + "【参考资料（已压缩，仅保留文章标题索引；如需原文请用 view_article 按文件名读取）】\n" + "\n".join(_ref_titles)
                if "【当前状态】" in _tail:
                    _sys_c += "\n【当前状态】" + _tail.split("【当前状态】", 1)[1]
                base.append({"role": "system", "content": _sys_c})
                sys_compacted = True
            else:
                base.append(m)
        elif r == "tool":
            c = str(m.get("content") or "")
            # 提取 view_article 已读文章信息（形如 "文件: xxx (共N字符, 位置: a-b)"）
            _mf = re.search(r'文件: ([^\s(]+)', c)
            _mp = re.search(r'位置: (\d+)-(\d+)', c)
            if _mf:
                read_manifest.append(f"{_mf.group(1)}[{_mp.group(1)}-{_mp.group(2)}]" if _mp else _mf.group(1))
            first = c.split("\n")[0][:80]
            if first:
                parts.append(first)
        elif r == "assistant" and (m.get("content") or "").strip():
            parts.append("asst:" + str(m.get("content"))[:80])
        i += 1
    if parts:
        base.append({"role": "assistant",
                     "content": "[上下文压缩：前述工具链关键产出] " + "; ".join(parts)})
    # token 节省整改：注入已读文章清单
    if read_manifest:
        base.append({
            "role": "user",
            "content": "【已读文章清单（压缩保留）】本线已读取过以下文章片段，不要重复读取相同内容：\n- "
                       + "\n- ".join(read_manifest[:20])
        })
    result = base + messages[cut:]
    # 压缩后给所有 assistant 消息补空 reasoning_content
    # DeepSeek 思考模式要求所有 assistant 消息都带 reasoning_content
    for m in result:
        if m.get("role") == "assistant" and "reasoning_content" not in m:
            m["reasoning_content"] = ""
    return result


def run_llm_five_line(
    gap_id: str,
    title: str,
    anchors: List[str],
    target: str,
    base_system_prompt: str,
    client,
    model: str,
    tools: Optional[list],
    execute_tool: Callable,
    max_tool_chain: int = 6,
    logger=None,
    embed_fn=None,
    semantic_threshold: float = 0.80,
    line_compact_threshold: int = 30000,
    line_compact_keep_recent: int = 2,
    session_mode: str = 'derive',
) -> Dict:
    """跑完五线并行推导，横向比较，判收敛，持久化，返回汇总。"""
    log = logger or (lambda *a, **k: None)
    log(f"[WB] 五线推导 begin gap_id={gap_id} anchors={anchors} target={target[:40]}")
    # ---------- 建台 + 五线模板 ----------
    try:
        flow = DerivationFlow.create_task(gap_id, title, anchors, target, "DERIVATION")
    except Exception as _ex:
        log(f"[WB] 建台失败(create_task) gap_id={gap_id}: {_ex}")
        return {"id": gap_id, "title": title, "target": target,
                "closed": [], "dead": [], "lines": {}, "cross_support": [],
                "converged": False, "converge_check": None, "audit_stats": {},
                "state_path": "", "report_md": "", "conclusion": ""}
    wb = flow.wb

    def _run_line(line_id: str, angle: str, angle_desc: str) -> Optional[str]:
        """单线工具链调用，返回该线最终文本。"""
        sys_prompt = (
            base_system_prompt
            + f"\n\n【五线并行推导 · 线{line_id} · {angle}】\n角度说明：{angle_desc}"
            + _LINE_DISCIPLINE
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"从「{angle}」的角度推导：{target}"},
        ]
        api_params: Dict = {"model": model, "messages": messages}
        if tools:
            api_params["tools"] = tools
        try:
            for _r in range(1, max_tool_chain + 1):
                resp = client.chat.completions.create(**api_params)
                content = resp.choices[0].message.content or ""
                tcs = getattr(resp.choices[0].message, "tool_calls", None)
                if (not content or content.strip() == "") and tcs:
                    asst = {"role": "assistant", "content": None, "tool_calls": [], "reasoning_content": ""}
                    for tc in tcs:
                        asst["tool_calls"].append({"id": tc.id, "type": "function",
                                                   "function": {"name": tc.function.name,
                                                                "arguments": tc.function.arguments}})
                    messages.append(asst)
                    for tc in tcs:
                        try:
                            _args = json.loads(tc.function.arguments or "{}")
                        except Exception:
                            _args = {}
                        # token 节省整改：按线传独立 session_id（线间 calculate_math 变量互不污染）
                        _line_sid = f"wb:{gap_id}:line{line_id}"
                        try:
                            from tools import set_session_mode
                            set_session_mode(_line_sid, session_mode)
                        except Exception:
                            pass
                        try:
                            result = execute_tool(tc.function.name, _args, session_id=_line_sid)
                        except TypeError:
                            result = execute_tool(tc.function.name, _args)
                        messages.append({"role": "tool", "tool_call_id": tc.id,
                                         "content": str(result)})
                    # C 类：工具链历史超过阈值时压缩早期轮次（保留最近 keep_recent 轮完整）
                    _before = sum(len(str(m.get("content") or "")) for m in messages)
                    messages = _maybe_compact_line_history(messages, line_compact_threshold, line_compact_keep_recent)
                    _after = sum(len(str(m.get("content") or "")) for m in messages)
                    if _after < _before:
                        _kept_rounds = sum(1 for _m in messages if _m.get("tool_calls"))
                        log(f"[WB:{line_id}] 上下文压缩 #{_r} 轮: {_before}→{_after} 字符 (保留 {_kept_rounds} 轮工具往返)")
                    api_params["messages"] = messages
                    log(f"[WB:{line_id}] 工具调用 #{_r}: {len(tcs)} 个")
                    continue
                return content
            return None
        except Exception as ex:
            log(f"[WB:{line_id}] 单线调用失败: {ex}")
            return None

    # ---------- 五线各自推导 ----------
    results: Dict[str, Dict] = {}
    closed: List[str] = []
    dead: List[str] = []
    for line_id, angle, angle_desc in DERIVATION_LINES:
        text = _run_line(line_id, angle, angle_desc)
        if text is None:
            wb.push_result(line_id, "单线推导调用失败", "LLM五线推导", EV_FAILED)
            results[line_id] = {"status": LINE_PARTIAL, "text": "调用失败"}
            continue
        is_dead = bool(_DEAD_PAT.search(text))
        conclusion = ""
        _m = re.search(r"【线结论】[：:]?\s*(.+)", text)
        if _m:
            conclusion = _m.group(1).strip()
        elif is_dead:
            _dm = re.search(r"【死胡同】[：:]?\s*(.+)", text)
            conclusion = _dm.group(1).strip() if _dm else "该角度打不通"
        else:
            conclusion = (text.strip().splitlines() or [""])[-1][:120]
        wb.push_result(line_id, conclusion, "LLM五线推导", EV_VERIFIED if not is_dead else EV_OUTSCOPE)
        if is_dead:
            wb.mark_dead_end(line_id, conclusion)
            dead.append(line_id)
            results[line_id] = {"status": LINE_DEAD, "text": text, "conclusion": conclusion}
        else:
            wb.close_line(line_id, conclusion)
            closed.append(line_id)
            results[line_id] = {"status": LINE_CLOSED, "text": text, "conclusion": conclusion}
        log(f"[WB] 线{line_id}「{angle}」={'死胡同' if is_dead else '闭合'}: {conclusion[:60]}")

    # ---------- 横向比较：跨线交叉印证聚类 ----------
    # 三轨信号（由硬到软，只有更强信号不足时才启用更弱的语义轨道）：
    #   ① 关键符号硬碰撞（θ/α/κ/Λ 同符号）
    #   ② 关键短语 token 重叠（≥2 个）
    #   ③ 语义相似度软碰撞（用 embedding，识别"用词不同但意思相同"）
    cross = []
    symbol_hits: List[dict] = []   # ① 符号碰撞
    token_clusters: List[dict] = []  # ② token 重叠簇
    _sem_vecs = {}                 # ③ 结论 embedding 缓存（懒加载）

    def _get_vec(line_id: str) -> Optional[list]:
        """懒加载某条闭合线结论的 embedding 向量（带失败兜底）。"""
        if not embed_fn:
            return None
        if line_id not in _sem_vecs:
            try:
                _text = results[line_id].get("conclusion") or ""
                _r = embed_fn(_text)
                _v = (_r[0] if isinstance(_r, list) and _r else None)
                _sem_vecs[line_id] = _v if (_v and not all(x == 0 for x in _v)) else None
            except Exception:
                _sem_vecs[line_id] = None
        return _sem_vecs[line_id]

    for lid in closed:
        note = results[lid].get("conclusion", "")
        n_toks = _tokenize(note)
        n_nums = set(_numb_claims(note))
        n_syms = _symbol_claims(note)
        # ① 符号硬碰撞：并入已有符号簇
        placed_sym = False
        for cl in symbol_hits:
            if n_syms & cl["syms"]:
                cl["members"].append(lid)
                cl["syms"] |= n_syms
                placed_sym = True
                break
        if not placed_sym:
            symbol_hits.append({"head": _normalize(note)[:40], "members": [lid],
                                "syms": n_syms})
        # ② token 重叠簇
        placed = False
        for cl in token_clusters:
            ov_tok = len(n_toks & cl["toks"])
            ov_num = len(n_nums & cl["nums"])
            if ov_num >= 1 or ov_tok >= 2:
                cl["members"].append(lid)
                cl["toks"] |= n_toks
                cl["nums"] |= n_nums
                placed = True
                break
        if not placed:
            token_clusters.append({"head": _normalize(note)[:40], "members": [lid],
                                   "toks": n_toks, "nums": n_nums})
    # 输出成簇（符号簇与 token 簇取成员集合并，避免重复）
    def _flush(_cls):
        _by_members: Dict[tuple, list] = {}
        for cl in _cls:
            _m = tuple(sorted(set(cl["members"])))
            if len(_m) >= 2:
                _by_members[_m] = cl
        for _m, cl in _by_members.items():
            cross.append({"conclusion": cl["head"],
                          "lines": list(_m), "signal": "symbol" if id(cl) in {id(c) for c in symbol_hits} else "token"})
    _flush([c for c in symbol_hits if len(c["members"]) >= 2])
    _flush([c for c in token_clusters if len(c["members"]) >= 2])

    # ③ 语义软碰撞：仅当硬信号无产出时，才用 embedding 发现"用词不同但语义相近"的簇
    #    避免软信号覆盖硬碰撞结论。
    _has_hard = any(c for c in cross if c.get("signal") in ("symbol", "token"))
    if (not _has_hard) and embed_fn and len(closed) >= 2:
        sem_clusters: List[dict] = []
        for lid in closed:
            v = _get_vec(lid)
            if not v:
                continue
            placed_sem = False
            for cl in sem_clusters:
                _ref = cl["vec"]
                if _cosine(v, _ref) >= semantic_threshold:
                    cl["members"].append(lid)
                    placed_sem = True
                    break
            if not placed_sem:
                sem_clusters.append({"head": _normalize(results[lid].get("conclusion", ""))[:40],
                                     "members": [lid], "vec": v})
        for cl in sem_clusters:
            _m = sorted(set(cl["members"]))
            if len(_m) >= 2:
                cross.append({"conclusion": cl["head"], "lines": _m, "signal": "semantic"})
        if cross:
            log(f"[WB] 语义软碰撞识别 {len(cross)} 簇（词面不同但语义相近，相似度≥{semantic_threshold}）")

    # 数值级交叉印证（同数值出现在 ≥2 条闭合线，更硬的证据）
    numeric_clusters: Dict[str, List[str]] = {}
    for lid in closed:
        for v in _numb_claims(results[lid].get("conclusion", "")):
            numeric_clusters.setdefault(v, []).append(lid)
    for v, members in numeric_clusters.items():
        uniq = sorted(set(members))
        if len(uniq) >= 2:
            cross.append({"conclusion": f"数值交叉印证 {v}", "lines": uniq, "signal": "numeric"})

    # ---------- 收敛判定（≥2 独立闭合线交叉印证；或 1 闭合 + ≥2 死胡同排除） ----------
    support = list(dict.fromkeys(
        m for c in cross if len(c["lines"]) >= 2 for m in c["lines"]))
    converged = False
    converge_check = None
    if len(support) >= 2:
        # 取 cross 中最强的簇头作为收敛结论
        best = max(cross, key=lambda c: len(c["lines"]))["conclusion"]
        converge_check = flow.converge(best, [results[s]["conclusion"] for s in support],
                                       support=list(set(support)))
        converged = bool(converge_check.get("ok"))
    elif len(closed) == 1 and len(dead) >= 2:
        solo = closed[0]
        converge_check = flow.converge(results[solo]["conclusion"],
                                       [results[solo]["conclusion"]], support=[solo])
        converged = bool(converge_check.get("ok"))

    # 尝试审计（仅当有证据时）
    try:
        _items, audit_stats = flow.audit()
    except Exception:
        audit_stats = {}

    # 持久化快照（内存仍为权威）
    reg = WorkbenchRegistry.instance()
    reg._workspaces[gap_id] = wb
    try:
        path = flow.save()
    except Exception as ex:
        log(f"[WB] 持久化失败: {ex}")
        path = ""

    report_md = ""
    try:
        report_md = flow._build_report_md()
    except Exception:
        pass

    log(f"[WB] 五线推导 end gap_id={gap_id} "
        f"闭合={len(closed)} 死胡同={len(dead)} 交叉={len(cross)} "
        f"收敛={converged} persist={'OK' if path else 'FAIL'}")

    return {
        "id": gap_id,
        "title": title,
        "target": target,
        "closed": closed,
        "dead": dead,
        "lines": {lid: results[lid].get("status") for lid in results},
        "cross_support": cross,
        "converged": converged,
        "converge_check": converge_check,
        "audit_stats": audit_stats,
        "state_path": path,
        "report_md": report_md,
        "conclusion": wb.gap.conclusion or (cross[0]["conclusion"] if cross else ""),
    }