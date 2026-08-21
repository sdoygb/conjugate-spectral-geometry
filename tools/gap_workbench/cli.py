#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gap_workbench 命令行：5线程推理工作台 + 反向审计

用法示例：
  # 新建缺口（锚点用 | 分隔多个）
  python3 tools/gap_workbench/cli.py new --id chiL --title "χ_L 定义" \
      --anchor "χ_L = 1.509e-10 m（10.8 构造 8.1）" --target "找到定义定理" --type NUMERIC

  # 按模板建 5 线
  python3 tools/gap_workbench/cli.py lines --id chiL

  # 推进结果 / 标记死胡同 / 闭合线
  python3 tools/gap_workbench/cli.py result --id chiL --line 线1 --content "..." --source "..."
  python3 tools/gap_workbench/cli.py deadend --id chiL --line 线2 --reason "数值巧合"
  python3 tools/gap_workbench/cli.py close --id chiL --line 线3 --conclusion "..."

  # 收敛（chain 用逗号分隔证据 ID）
  python3 tools/gap_workbench/cli.py converge --id chiL --conclusion "..." --chain E1,E3,E5

  # 反向审计 + 报告
  python3 tools/gap_workbench/cli.py audit --id chiL
  python3 tools/gap_workbench/cli.py report --id chiL
"""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gap_workbench import Workbench, WorkbenchError, suggest_lines  # noqa: E402
from gap_workbench.report import build_report  # noqa: E402
from gap_workbench.models import EV_VERIFIED, EV_FLAGGED, EV_FAILED, EV_OUTSCOPE  # noqa: E402

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


def state_path(gap_id: str) -> str:
    return os.path.join(STATE_DIR, f"{gap_id}.json")


def load_or_die(gap_id: str) -> Workbench:
    p = state_path(gap_id)
    if not os.path.exists(p):
        sys.exit(f"缺口 {gap_id} 不存在（{p}）。先用 new 创建。")
    return Workbench.load(p)


def cmd_new(args):
    anchors = [a.strip() for a in args.anchor.split("|") if a.strip()]
    wb = Workbench.create(args.id, args.title, anchors, args.target, args.gap_type)
    wb.save(state_path(args.id))
    print(f"✅ 工作台已创建：{args.id}（{args.title}）")
    print(f"  状态文件：{state_path(args.id)}")
    print("  下一步：lines 建 5 线，或逐个 line 手动添加")


def cmd_lines(args):
    wb = load_or_die(args.id)
    wb.add_lines_from_template(suggest_lines(wb.gap.gap_type))
    wb.save(state_path(args.id))
    for l in wb.gap.lines:
        print(f"  {l.id}【{l.hypothesis}】{l.angle}")


def cmd_line(args):
    wb = load_or_die(args.id)
    wb.add_line(args.line, args.hypothesis, args.angle)
    wb.save(state_path(args.id))
    print(f"✅ {args.line} 已添加：{args.hypothesis}")


def cmd_result(args):
    wb = load_or_die(args.id)
    status = {"verified": EV_VERIFIED, "flagged": EV_FLAGGED,
              "failed": EV_FAILED, "outscope": EV_OUTSCOPE}.get(args.status, EV_VERIFIED)
    ev = wb.push_result(args.line, args.content, args.source, status, args.note or "")
    wb.save(state_path(args.id))
    print(f"✅ {args.line} → {ev.id} 已缓存（{ev.status}）")


def cmd_deadend(args):
    wb = load_or_die(args.id)
    wb.mark_dead_end(args.line, args.reason)
    wb.save(state_path(args.id))
    print(f"💀 {args.line} 标记死胡同：{args.reason}")


def cmd_close(args):
    wb = load_or_die(args.id)
    wb.close_line(args.line, args.conclusion)
    wb.save(state_path(args.id))
    print(f"✅ {args.line} 闭合：{args.conclusion}")


def cmd_partial(args):
    wb = load_or_die(args.id)
    wb.partial_line(args.line, args.note or "")
    wb.save(state_path(args.id))
    print(f"🔶 {args.line} 部分采用：{args.note}")


def cmd_converge(args):
    wb = load_or_die(args.id)
    chain = [c.strip() for c in args.chain.split(",") if c.strip()] if args.chain else []
    support = [s.strip() for s in args.support.split(",") if s.strip()] if args.support else None
    check = wb.converge(args.conclusion, chain, support=support)
    wb.save(state_path(args.id))
    print(f"{'✅ 已收敛' if check['ok'] else '❌ 未收敛'}：{check['reason']}（{check.get('mode','-')}）")
    if not check["ok"]:
        print("  提示：正面收敛需 ≥2 条闭合支持线；排除收敛需 1 闭合 + ≥2 死胡同")
    if check.get("unmarked"):
        print(f"  ⚠️ 未标注闭合线（不在 support 中）：{check['unmarked']}")


def cmd_loc(args):
    wb = load_or_die(args.id)
    ev = wb.find_evidence(args.evidence)
    if ev is None:
        sys.exit(f"证据 {args.evidence} 不存在")
    ev.loc = args.loc
    wb.save(state_path(args.id))
    print(f"📌 {ev.id} 定位：{args.loc}")


def cmd_locate(args):
    wb = load_or_die(args.id)
    locs = wb.locate_all()
    ev_ids = [e.strip() for e in args.evidence.split(",")] if args.evidence else None
    for line in wb.gap.lines:
        for ev in line.results:
            if ev_ids and ev.id not in ev_ids:
                continue
            info = locs.get(ev.id)
            if not info:
                continue
            print(f"--- {ev.id}（{line.id}）{ev.loc} ---")
            if info["text"]:
                print(info["text"])
            else:
                print(f"[定位失败] {info['error']}")
            print()


def cmd_audit(args):
    wb = load_or_die(args.id)
    items, stats = wb.audit(include_adopted=not args.chain_only)
    wb.save(state_path(args.id))
    print(f"反向审计完成：✅ {stats['verified']} ｜ ⚠️ {stats['flagged']} ｜ "
          f"❌ {stats['failed']} ｜ 📌 {stats['outscope']}")
    for it in items:
        print(f"  {it.status} {it.link}：{it.evidence[:60]}" + (f"（{it.note}）" if it.note else ""))
    if args.locate:
        locs = wb.locate_all()
        for line in wb.gap.lines:
            for ev in line.results:
                info = locs.get(ev.id)
                if not info:
                    continue
                print(f"  ── {ev.id} 原文[{ev.loc}]"
                      + (f"（{info['error']}）" if info["error"] else "") + "：")
                if info["text"]:
                    print(f"     {info['text'][:220]}")


def cmd_report(args):
    wb = load_or_die(args.id)
    stats = None
    if wb.gap.audit:
        stats = {"verified": sum(1 for a in wb.gap.audit if a.status == EV_VERIFIED),
                 "flagged": sum(1 for a in wb.gap.audit if a.status == EV_FLAGGED),
                 "failed": sum(1 for a in wb.gap.audit if a.status == EV_FAILED),
                 "outscope": sum(1 for a in wb.gap.audit if a.status == EV_OUTSCOPE)}
    md = build_report(wb.gap, stats)
    out = args.out or os.path.join(STATE_DIR, f"{args.id}.md")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"📄 报告已写入：{out}")
    print(md)


def main():
    p = argparse.ArgumentParser(description="gap_workbench：5线程推理 + 反向审计")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--id", required=True)

    sp = sub.add_parser("new", help="新建缺口工作台")
    sp.add_argument("--id", required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--anchor", required=True, help="锚点，多个用 | 分隔")
    sp.add_argument("--target", required=True)
    sp.add_argument("--type", dest="gap_type", default="NUMERIC",
                    choices=["NUMERIC", "CLAIM", "FORMULA", "CONSISTENCY"])
    sp.set_defaults(func=cmd_new)

    sp = sub.add_parser("lines", help="按模板建 5 线")
    add_common(sp)
    sp.set_defaults(func=cmd_lines)

    sp = sub.add_parser("line", help="手动添加一条线")
    add_common(sp)
    sp.add_argument("--line", required=True)
    sp.add_argument("--hypothesis", required=True)
    sp.add_argument("--angle", default="")
    sp.set_defaults(func=cmd_line)

    sp = sub.add_parser("result", help="推进一条线：缓存中间结果")
    add_common(sp)
    sp.add_argument("--line", required=True)
    sp.add_argument("--content", required=True)
    sp.add_argument("--source", required=True)
    sp.add_argument("--status", default="verified",
                    choices=["verified", "flagged", "failed", "outscope"])
    sp.add_argument("--note", default="")
    sp.set_defaults(func=cmd_result)

    sp = sub.add_parser("deadend", help="标记死胡同")
    add_common(sp)
    sp.add_argument("--line", required=True)
    sp.add_argument("--reason", required=True)
    sp.set_defaults(func=cmd_deadend)

    sp = sub.add_parser("close", help="闭合一条线（给出线结论）")
    add_common(sp)
    sp.add_argument("--line", required=True)
    sp.add_argument("--conclusion", required=True)
    sp.set_defaults(func=cmd_close)

    sp = sub.add_parser("partial", help="部分采用一条线")
    add_common(sp)
    sp.add_argument("--line", required=True)
    sp.add_argument("--note", default="")
    sp.set_defaults(func=cmd_partial)

    sp = sub.add_parser("converge", help="设置收敛结论与依赖链（执行判据检查）")
    add_common(sp)
    sp.add_argument("--conclusion", required=True)
    sp.add_argument("--chain", default="", help="证据 ID，逗号分隔，如 E1,E3,E5")
    sp.add_argument("--support", default="", help="支持结论的线 ID，逗号分隔，如 线3,线5")
    sp.set_defaults(func=cmd_converge)

    sp = sub.add_parser("loc", help="给证据设置行号定位（如 10.54:183）")
    add_common(sp)
    sp.add_argument("--evidence", required=True)
    sp.add_argument("--loc", required=True,
                    help="行号定位：文章:行号 或 文章:起-止，如 10.54:183、10.8:468-476")
    sp.set_defaults(func=cmd_loc)

    sp = sub.add_parser("locate", help="列出证据的行号定位原文（审计快速核实）")
    add_common(sp)
    sp.add_argument("--evidence", default="", help="证据 ID，逗号分隔（默认全部）")
    sp.set_defaults(func=cmd_locate)

    sp = sub.add_parser("audit", help="反向审计（全内存）")
    add_common(sp)
    sp.add_argument("--chain-only", action="store_true", help="只审计主链，不审计采用线")
    sp.add_argument("--locate", action="store_true", help="审计后附带证据的行号定位原文")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("report", help="生成 Markdown 报告")
    add_common(sp)
    sp.add_argument("--out", default="")
    sp.set_defaults(func=cmd_report)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
