#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown 报告生成：战况表 + 证据缓存 + 收敛判断 + 反向审计表"""
from __future__ import annotations
from typing import Dict
from .models import Gap, GAP_TYPES, LINE_OPEN, LINE_DEAD, LINE_CLOSED, LINE_PARTIAL


def _fmt_ev_status_icon(status: str) -> str:
    return status.split(" ")[0] if " " in status else status


def build_report(gap: Gap, audit_stats: Dict = None) -> str:
    t = gap.gap_type
    type_name = GAP_TYPES.get(t, t)
    status = "✅ 已收敛" if gap.converged else "⏳ 未收敛"
    lines = []
    lines.append(f"# 推理工作台：{gap.title}")
    lines.append("")
    lines.append(f"- **缺口 ID**：{gap.id} ｜ **类型**：{type_name} ｜ **状态**：{status}")
    if gap.converged_note:
        lines.append(f"- **收敛判据**：{gap.converged_note}")
    lines.append("")
    lines.append("## 锚点（已知量）")
    lines.append("")
    for a in gap.anchors:
        lines.append(f"- {a}")
    lines.append("")
    lines.append(f"## 目标\n\n{gap.target}\n")

    # ---- 五线战况 ----
    lines.append("## 五线战况")
    lines.append("")
    lines.append("| 线 | 假设 | 状态 | 关键结果/结论 |")
    lines.append("|---|---|---|---|")
    for l in gap.lines:
        last = l.results[-1].content[:70] if l.results else ""
        note = l.note if l.note else last
        lines.append(f"| {l.id} | {l.hypothesis} | {l.status} | {note} |")
    lines.append("")

    # ---- 证据缓存 ----
    lines.append("## 证据缓存")
    lines.append("")
    lines.append("| ID | 线 | 内容 | 来源 | 定位 | 状态 |")
    lines.append("|---|---|---|---|---|---|")
    for l in gap.lines:
        for ev in l.results:
            lines.append(f"| {ev.id} | {l.id} | {ev.content[:90]} | {ev.source} | {ev.loc or '-'} | {ev.status} |")
    lines.append("")

    # ---- 收敛结论 ----
    lines.append("## 收敛结论")
    lines.append("")
    if gap.conclusion:
        lines.append(f"{gap.conclusion}")
        if gap.chain:
            lines.append("")
            lines.append(f"依赖链：{' → '.join(gap.chain)}")
    else:
        lines.append("（未收敛）")
    lines.append("")

    # ---- 反向审计 ----
    lines.append("## 反向审计（全内存）")
    lines.append("")
    if gap.audit:
        lines.append("| 环节 | 证据 | 状态 | 备注 |")
        lines.append("|---|---|---|---|")
        for it in gap.audit:
            lines.append(f"| {it.link} | {it.evidence} | {it.status} | {it.note} |")
        lines.append("")
        if audit_stats:
            s = audit_stats
            lines.append(f"统计：✅ {s['verified']} ｜ ⚠️ {s['flagged']} ｜ "
                         f"❌ {s['failed']} ｜ 📌 {s['outscope']}")
    else:
        lines.append("（尚未执行审计）")
    lines.append("")
    return "\n".join(lines)
