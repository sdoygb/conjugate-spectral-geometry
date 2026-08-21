#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workbench 核心：工作台生命周期（建台→推进→收敛→审计→持久化）"""
from __future__ import annotations
import json
import os
import re
from typing import Dict, List, Optional, Tuple

from .models import (
    Gap, Line, Evidence, AuditItem,
    LINE_OPEN, LINE_DEAD, LINE_CLOSED, LINE_PARTIAL,
    EV_VERIFIED, EV_FLAGGED, EV_FAILED, EV_OUTSCOPE,
    gap_to_dict, gap_from_dict,
)


# ---------- 行号定位（locate）：审计时快速核实原文，省整段重读 ----------

_LOC_RE = re.compile(r"^([0-9.]+):(\d+)(?:-(\d+))?$")


def find_articles_dir() -> Optional[str]:
    """探测文章目录：app/articles 优先，其次 articles"""
    for d in ("app/articles", "articles"):
        if os.path.isdir(d):
            return d
    return None


def resolve_article(article_id: str) -> Optional[str]:
    """文章编号 → 文件路径（CN 版优先）"""
    d = find_articles_dir()
    if not d:
        return None
    cands = [f for f in os.listdir(d)
             if f.startswith(article_id + "_") and f.endswith(".md")]
    if not cands:
        return None
    cands.sort(key=lambda f: 0 if "_CN_" in f else 1)
    return os.path.join(d, cands[0])


def parse_loc(loc: str) -> Optional[Tuple[str, int, int]]:
    """解析行号定位：10.54:183 或 10.54:180-190 → (文章, 起, 止)"""
    m = _LOC_RE.match(loc.strip())
    if not m:
        return None
    art, s, e = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
    return art, s, e


def read_lines(path: str, start: int, end: int) -> str:
    """按 1-based 行号读取原文行"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[start - 1:end])


class WorkbenchError(Exception):
    pass


class Workbench:
    """缺口工作台：5线程并行推理 + 反向审计协议 的状态机"""

    def __init__(self, gap: Gap):
        self.gap = gap
        self._support: Optional[List[str]] = None

    # ---------- 创建 / 持久化 ----------

    @classmethod
    def create(cls, gap_id: str, title: str, anchors: List[str], target: str,
               gap_type: str = "NUMERIC") -> "Workbench":
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gap = Gap(id=gap_id, title=title, anchors=list(anchors), target=target,
                  gap_type=gap_type, created=now, updated=now)
        return cls(gap)

    @classmethod
    def load(cls, path: str) -> "Workbench":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(gap_from_dict(data))

    def save(self, path: str) -> None:
        from datetime import datetime
        self.gap.updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(gap_to_dict(self.gap), f, ensure_ascii=False, indent=2)

    # ---------- 线管理 ----------

    def add_line(self, line_id: str, hypothesis: str, angle: str) -> Line:
        if any(l.id == line_id for l in self.gap.lines):
            raise WorkbenchError(f"线 {line_id} 已存在")
        line = Line(id=line_id, hypothesis=hypothesis, angle=angle)
        self.gap.lines.append(line)
        return line

    def get_line(self, line_id: str) -> Line:
        for l in self.gap.lines:
            if l.id == line_id:
                return l
        raise WorkbenchError(f"线 {line_id} 不存在")

    def add_lines_from_template(self, suggestions: List[Tuple[str, str, str]]) -> None:
        """按模板批量建线：suggestions = [(线id, 假设, 角度)]"""
        for lid, hyp, angle in suggestions:
            self.add_line(lid, hyp, angle)

    # ---------- 结果推进 ----------

    def push_result(self, line_id: str, content: str, source: str,
                    status: str = EV_VERIFIED, note: str = "") -> Evidence:
        line = self.get_line(line_id)
        idx = 1 + sum(len(l.results) for l in self.gap.lines)  # 全局编号，防跨线重复
        ev = Evidence(id=f"E{idx}", line_id=line_id, content=content,
                      source=source, status=status, note=note)
        line.results.append(ev)
        return ev

    def mark_dead_end(self, line_id: str, reason: str) -> None:
        line = self.get_line(line_id)
        line.status = LINE_DEAD
        line.note = reason

    def close_line(self, line_id: str, conclusion: str) -> None:
        line = self.get_line(line_id)
        line.status = LINE_CLOSED
        line.note = conclusion

    def partial_line(self, line_id: str, note: str) -> None:
        line = self.get_line(line_id)
        line.status = LINE_PARTIAL
        line.note = note

    def find_evidence(self, ev_id: str) -> Optional[Evidence]:
        for line in self.gap.lines:
            for ev in line.results:
                if ev.id == ev_id:
                    return ev
        return None

    def locate_all(self) -> Dict[str, Dict]:
        """定位所有带 loc 的证据 → {ev_id: {loc, text, error}}（读文章文件，不检索）"""
        out: Dict[str, Dict] = {}
        for line in self.gap.lines:
            for ev in line.results:
                if not ev.loc:
                    continue
                info = {"loc": ev.loc, "text": "", "error": ""}
                parsed = parse_loc(ev.loc)
                if parsed is None:
                    info["error"] = f"loc 格式无效（应为 文章:行号 或 文章:起-止）：{ev.loc}"
                else:
                    art, s, e = parsed
                    path = resolve_article(art)
                    if path is None:
                        info["error"] = f"app/articles 下未找到文章 {art}"
                    else:
                        try:
                            info["text"] = read_lines(path, s, e).strip()
                        except Exception as ex:
                            info["error"] = f"读取失败：{ex}"
                out[ev.id] = info
        return out

    # ---------- 收敛判据 v2（硬性规则） ----------

    def check_convergence(self) -> Dict:
        """
        判据 v2：
        - 正面收敛：≥2 条支持线（converge 时显式指定）全部闭合
        - 排除收敛：1 条支持线闭合 + ≥2 条死胡同（多条独立排除同一方向）
        - 未标注的闭合线记 unmarked（警告，不阻断）
        """
        support = self._support or []
        closed_ids = {l.id for l in self.gap.lines if l.status == LINE_CLOSED}
        dead_ids = {l.id for l in self.gap.lines if l.status == LINE_DEAD}
        if not support:
            return {"ok": False, "mode": "-",
                    "reason": "未指定支持线（converge 需 --support）",
                    "unmarked": sorted(closed_ids)}
        bad = [s for s in support if s not in closed_ids]
        if bad:
            return {"ok": False, "mode": "-",
                    "reason": f"支持线未闭合: {bad}", "unmarked": []}
        if len(support) >= 2:
            ok, mode = True, "正面收敛"
            reason = f"{len(support)} 条闭合线独立支持结论（正面收敛）"
        elif len(support) == 1 and len(dead_ids) >= 2:
            ok, mode = True, "排除收敛"
            reason = f"1 条闭合线 + {len(dead_ids)} 条独立死胡同（排除式收敛）"
        else:
            ok, mode = False, "-"
            reason = f"支持线 {len(support)} 条（正面需 ≥2；排除需 1 + ≥2 死胡同）"
        unmarked = sorted(closed_ids - set(support))
        return {"ok": ok, "mode": mode, "reason": reason, "unmarked": unmarked}

    def converge(self, conclusion: str, chain: List[str],
                 support: Optional[List[str]] = None) -> Dict:
        """设置结论与依赖链，执行收敛判据检查。support：支持结论的线 ID 列表"""
        self.gap.conclusion = conclusion
        self.gap.chain = list(chain)
        self._support = list(support) if support else None
        check = self.check_convergence()
        self.gap.converged = check["ok"]
        self.gap.converged_note = check["reason"]
        return check

    # ---------- 反向审计（全内存，无外部检索） ----------

    def audit(self, include_adopted: bool = True) -> Tuple[List[AuditItem], Dict]:
        """
        反向审计：从收敛结论反向检查推导链。
        1) 主链：结论 chain 中的每个证据逐环节验证（状态映射）
        2) 反推：被采用线（闭合/部分采用）中未入链的结果也检查（防止漏检）
        全部基于工作台缓存，不发起任何外部检索。
        """
        items: List[AuditItem] = []
        # 1. 主链逐环节
        for ev_id in self.gap.chain:
            ev = self.find_evidence(ev_id)
            if ev is None:
                items.append(AuditItem(ev_id, "链条引用缺失", EV_FAILED,
                                       "chain 引用了不存在的证据 → 链条断裂"))
            else:
                items.append(AuditItem(ev.id, ev.content[:80], ev.status, ev.note))
        # 2. 采用线反推
        if include_adopted:
            for line in self.gap.lines:
                if line.status in (LINE_CLOSED, LINE_PARTIAL):
                    for ev in line.results:
                        if ev.id not in self.gap.chain:
                            items.append(AuditItem(
                                ev.id, ev.content[:80], ev.status,
                                (ev.note + "；" if ev.note else "") + "采用但未入结论链"))
        stats = {"verified": 0, "flagged": 0, "failed": 0, "outscope": 0}
        for it in items:
            if it.status == EV_VERIFIED:
                stats["verified"] += 1
            elif it.status == EV_FLAGGED:
                stats["flagged"] += 1
            elif it.status == EV_FAILED:
                stats["failed"] += 1
            else:
                stats["outscope"] += 1
        self.gap.audit = items
        return items, stats

    # ---------- 摘要 ----------

    def summary(self) -> Dict:
        lines = []
        for l in self.gap.lines:
            lines.append({"id": l.id, "hypothesis": l.hypothesis,
                          "status": l.status, "note": l.note,
                          "n_results": len(l.results)})
        return {"id": self.gap.id, "title": self.gap.title,
                "converged": self.gap.converged, "lines": lines,
                "conclusion": self.gap.conclusion}
