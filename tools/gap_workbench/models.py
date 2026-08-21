#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据模型：缺口 / 推理线 / 证据 / 审计项（Python 3.9 兼容）"""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# ---------- 线状态 ----------
LINE_OPEN = "推进中"
LINE_DEAD = "死胡同"
LINE_CLOSED = "闭合"
LINE_PARTIAL = "部分采用"

# ---------- 证据/审计状态 ----------
EV_VERIFIED = "✅ 已验证"
EV_FLAGGED = "⚠️ 有出入"
EV_FAILED = "❌ 验证失败"
EV_OUTSCOPE = "📌 超范围"

# ---------- 缺口类型 ----------
GAP_TYPES = {
    "NUMERIC": "数值来源型",
    "CLAIM": "声称验证型",
    "FORMULA": "公式型",
    "CONSISTENCY": "一致性型",
}


@dataclass
class Evidence:
    """证据：某条线产生的中间结果（含来源与验证状态）"""
    id: str                    # E1, E2, ...
    line_id: str               # 所属线
    content: str               # 结果内容
    source: str                # 来源（文章/计算/检索，标注缓存位置）
    status: str = EV_VERIFIED  # 验证状态
    note: str = ""             # 备注（精度标注、待查项等）
    loc: str = ""              # 行号定位（如 10.54:183、10.8:468-476）


@dataclass
class Line:
    """推理线：一个独立假设/角度"""
    id: str                    # 线1..线5
    hypothesis: str            # 假设/角度名
    angle: str                 # 该角度要回答的问题
    status: str = LINE_OPEN
    results: List[Evidence] = field(default_factory=list)
    note: str = ""             # 闭合/死胡同时的结论或原因


@dataclass
class AuditItem:
    """反向审计项"""
    link: str                  # 环节（证据 ID 或环节名）
    evidence: str              # 证据内容摘要
    status: str                # EV_*
    note: str = ""


@dataclass
class Gap:
    """缺口工作台"""
    id: str
    title: str
    anchors: List[str]         # 锚点（已知量，含来源）
    target: str                # 目标
    gap_type: str = "NUMERIC"
    lines: List[Line] = field(default_factory=list)
    conclusion: str = ""       # 收敛结论
    chain: List[str] = field(default_factory=list)  # 结论依赖的证据 ID 链
    converged: bool = False
    converged_note: str = ""   # 收敛判据检查结果
    audit: List[AuditItem] = field(default_factory=list)
    created: str = ""
    updated: str = ""


# ---------- 工具函数 ----------

def normalize(text: str) -> str:
    """规范化文本用于比较：去空白/标点/LaTeX 标记"""
    t = re.sub(r"\$[^$]*\$", "", text)
    t = re.sub(r"\\[a-zA-Z]+", "", t)
    t = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff.%=<>≈]", "", t)
    return t


def evidence_to_dict(ev: Evidence) -> dict:
    return asdict(ev)


def evidence_from_dict(d: dict) -> Evidence:
    return Evidence(**d)


def line_to_dict(line: Line) -> dict:
    d = asdict(line)
    d["results"] = [evidence_to_dict(e) for e in line.results]
    return d


def line_from_dict(d: dict) -> Line:
    d = dict(d)
    d["results"] = [evidence_from_dict(e) for e in d.get("results", [])]
    return Line(**d)


def gap_to_dict(gap: Gap) -> dict:
    d = asdict(gap)
    d["lines"] = [line_to_dict(l) for l in gap.lines]
    d["audit"] = [asdict(a) for a in gap.audit]
    return d


def gap_from_dict(d: dict) -> Gap:
    d = dict(d)
    d["lines"] = [line_from_dict(l) for l in d.get("lines", [])]
    d["audit"] = [AuditItem(**a) for a in d.get("audit", [])]
    return Gap(**d)
