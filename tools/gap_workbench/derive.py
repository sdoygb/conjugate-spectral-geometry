#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推导工作流：5线并行推导 → 结果全保留 → 横向比较 → 收敛判据 → 反向审计 → 报告

推导任务自动调用方式（一次调用完成全流程）：
  1) create_task : 建台 + 按推导策略模板自动建 5 线（闭式/微分/几何/最优参数/结构）
  2) run_verifiers: 自动执行各线验证器（数值验证），结果全部保留（含失败/死胡同）
  3) compare     : 横向比较各线（状态/结论/交叉印证/死胡同）
  4) converge    : 收敛判据 v2（≥2 闭合支持 或 1 闭合 + ≥2 死胡同）
  5) audit       : 反向审计结论链
  6) report      : 生成 Markdown 报告（含比较表）

验证器约定：verifiers = {线id: {"code": python代码, "source": 来源, "dead_on_fail": bool}}
  code 内定义 run() 返回 dict：
    {"values": {名称: 数值}, "conclusion": 结论文本, "dead": bool, "reason": 死胡同原因}
  验证器失败 → 证据以 EV_FAILED 保留（不丢）；dead_on_fail=True 时同时标记死胡同。
"""
from __future__ import annotations
import os
import traceback
from typing import Dict, List, Optional, Tuple

from .models import (
    LINE_OPEN, LINE_DEAD, LINE_CLOSED, LINE_PARTIAL,
    EV_VERIFIED, EV_FLAGGED, EV_FAILED, EV_OUTSCOPE,
)
from .workbench import Workbench
from .templates import DERIVATION_LINES as DERIVATION_STRATEGIES


def suggest_derivation_lines() -> List[Tuple[str, str, str]]:
    """推导型缺口的 5 线建议 [(线id, 策略名, 角度描述)]（策略定义见 templates.py）"""
    return [list(t) for t in DERIVATION_STRATEGIES]


class DerivationFlow:
    """推导工作流：在 Workbench 之上叠加 自动验证器 + 横向比较"""

    def __init__(self, wb: Workbench):
        self.wb = wb

    # ---------- 创建 ----------

    @classmethod
    def create_task(cls, gap_id: str, title: str, anchors: List[str], target: str,
                    gap_type: str = "DERIVATION",
                    use_template: bool = True) -> "DerivationFlow":
        """建台 + 按推导策略模板自动建 5 线"""
        wb = Workbench.create(gap_id, title, anchors, target, gap_type)
        if use_template:
            wb.add_lines_from_template(suggest_derivation_lines())
        return cls(wb)

    # ---------- 验证器自动执行（结果全保留） ----------

    def run_verifiers(self, verifiers: Dict[str, Dict]) -> Dict[str, Dict]:
        """执行各线验证器。每条线的结果（成功/失败/死胡同）全部保留为证据。
        返回 {线id: {"ok": bool, "evidence": E#id, "values": {...} | "error": str, "dead": bool}}"""
        out: Dict[str, Dict] = {}
        for lid, spec in verifiers.items():
            code = spec.get("code", "")
            source = spec.get("source", "验证器自动执行")
            try:
                ns: Dict = {}
                exec(code, ns)
                run = ns.get("run")
                if not callable(run):
                    raise ValueError("验证器必须定义 run() 函数")
                result = run()
                if not isinstance(result, dict):
                    result = {"values": {"value": result}}
                values = result.get("values", {})
                vstr = "；".join(f"{k}={v}" for k, v in values.items())
                conclusion = result.get("conclusion", "验证器执行成功")
                if result.get("dead"):
                    self.wb.mark_dead_end(lid, result.get("reason", "验证器判定死胡同"))
                    status = EV_OUTSCOPE
                else:
                    status = EV_VERIFIED
                ev = self.wb.push_result(
                    lid, f"{conclusion}" + (f"（{vstr}）" if vstr else ""), source, status)
                if spec.get("auto_close", True) and not result.get("dead"):
                    self.wb.close_line(lid, conclusion)
                out[lid] = {"ok": True, "evidence": ev.id, "values": values,
                            "dead": bool(result.get("dead"))}
            except Exception as ex:
                tb = traceback.format_exc(limit=3)
                ev = self.wb.push_result(lid, f"验证器失败：{ex}", source, EV_FAILED, tb[-500:])
                out[lid] = {"ok": False, "evidence": ev.id, "error": str(ex),
                            "dead": False}
                if spec.get("dead_on_fail", False):
                    self.wb.mark_dead_end(lid, f"验证器失败：{ex}")
        return out

    # ---------- 横向比较 ----------

    def compare(self) -> Dict:
        """横向比较：各线状态/结论/关键数值 + 交叉印证（≥2 线同结论）+ 死胡同"""
        lines = []
        for l in self.wb.gap.lines:
            results = [{"id": e.id, "content": e.content, "status": e.status}
                       for e in l.results]
            lines.append({"id": l.id, "hypothesis": l.hypothesis,
                          "status": l.status, "note": l.note, "results": results})
        clusters: Dict[str, List[str]] = {}
        for l in self.wb.gap.lines:
            if l.status == LINE_CLOSED and l.note:
                key = l.note.strip()[:40]
                clusters.setdefault(key, []).append(l.id)
        cross = [{"conclusion": k, "lines": v} for k, v in clusters.items() if len(v) >= 2]
        dead = [l.id for l in self.wb.gap.lines if l.status == LINE_DEAD]
        return {"lines": lines, "cross_support": cross, "dead_ends": dead,
                "n_closed": sum(1 for l in self.wb.gap.lines if l.status == LINE_CLOSED),
                "n_dead": len(dead)}

    # ---------- 收敛 / 审计 ----------

    def converge(self, conclusion: str, chain: List[str],
                 support: Optional[List[str]] = None) -> Dict:
        """设置收敛结论与依赖链，执行收敛判据 v2（复用 Workbench）"""
        return self.wb.converge(conclusion, chain, support)

    def audit(self) -> Tuple[List, Dict]:
        """反向审计结论链（复用 Workbench，全内存）"""
        return self.wb.audit()

    # ---------- 报告 ----------

    def report(self, out_path: Optional[str] = None) -> str:
        """生成 Markdown 报告（五线表 + 横向比较 + 收敛 + 审计 + 证据明细）"""
        md = self._build_report_md()
        if out_path:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
        return md

    def _build_report_md(self) -> str:
        g = self.wb.gap
        cmp = self.compare()
        L = []
        L.append(f"# 推导工作台：{g.title}")
        L.append("")
        L.append(f"- ID：`{g.id}` ｜ 类型：{g.gap_type}")
        L.append(f"- 锚点：{'；'.join(g.anchors)}")
        L.append(f"- 目标：{g.target}")
        L.append(f"- 状态：{'✅ 已收敛' if g.converged else '❌ 未收敛'}（{g.converged_note or '未检查'}）")
        L.append("")
        L.append("## 五线推进")
        L.append("")
        L.append("| 线 | 策略 | 状态 | 结果/结论 |")
        L.append("|:--|:--|:--|:--|")
        for l in g.lines:
            last = l.results[-1].content[:60] if l.results else ""
            L.append(f"| {l.id} | {l.hypothesis} | {l.status} | {last} |")
        L.append("")
        L.append("## 横向比较")
        L.append("")
        if cmp["cross_support"]:
            L.append("**交叉印证（≥2 线同结论）**：")
            for c in cmp["cross_support"]:
                L.append(f"- 「{c['conclusion']}」← {','.join(c['lines'])}")
        else:
            L.append("无 ≥2 线同结论的交叉印证。")
        if cmp["dead_ends"]:
            L.append("")
            L.append(f"**死胡同（排除性证据）**：{','.join(cmp['dead_ends'])}")
        L.append("")
        L.append("## 收敛结论")
        L.append("")
        L.append(g.conclusion or "（未设置）")
        L.append("")
        L.append(f"依赖链：{', '.join(g.chain) if g.chain else '（未设置）'}")
        L.append("")
        L.append("## 反向审计")
        L.append("")
        if g.audit:
            stats = {"verified": 0, "flagged": 0, "failed": 0, "outscope": 0}
            for it in g.audit:
                key = {"✅ 已验证": "verified", "⚠️ 有出入": "flagged",
                       "❌ 验证失败": "failed", "📌 超范围": "outscope"}.get(it.status, "verified")
                stats[key] += 1
            L.append(f"✅ {stats['verified']} ｜ ⚠️ {stats['flagged']} ｜ "
                     f"❌ {stats['failed']} ｜ 📌 {stats['outscope']}")
            for it in g.audit:
                L.append(f"- {it.status} `{it.link}`：{it.evidence[:70]}")
        else:
            L.append("（未执行）")
        L.append("")
        L.append("## 证据明细")
        L.append("")
        for l in g.lines:
            L.append(f"### {l.id}【{l.hypothesis}】{l.status}")
            if l.note:
                L.append(f"*{l.note}*")
            for e in l.results:
                L.append(f"- `{e.id}` {e.status}：{e.content}（{e.source}）")
            L.append("")
        return "\n".join(L)

    # ---------- 持久化 ----------

    def save(self, path: Optional[str] = None) -> str:
        p = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "state", f"{self.wb.gap.id}.json")
        self.wb.save(p)
        return p
