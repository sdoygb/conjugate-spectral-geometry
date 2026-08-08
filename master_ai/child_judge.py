#!/usr/bin/env python3
"""
child_judge.py — 子AI判定接口（直接操作主库，shell + 落盘）

LLM 退役后（2026-08-05），入库判据由子AI执行：
  - A0 类（局部代数命题）：推导链逐步骤自洽 + 依赖闭合 → 圆满
  - A1 类（整体拓扑命题）：Berry 相位 2π 闭环 + 依赖闭合 → 圆满

用法：
  python3 child_judge.py list                     # 列出待判定公式（awaiting_child_judge）
  python3 child_judge.py show <submission_id>     # 显示完整判定材料
  python3 child_judge.py prepare <submission_id>  # 触发机械检查+依赖核对，挂起等待判定
  python3 child_judge.py prepare_all              # 所有 pending → 挂起
  python3 child_judge.py judge <submission_id> \
      --verdict promote|reject|dependency_gap \
      [--level 初圆满|中圆满|上圆满] --reason "..."   # 提交判定
  python3 child_judge.py rejudge <永久编号> \
      --verdict keep|suspend --level ... --reason "..."  # 存量真理重新判定
  python3 child_judge.py log                      # 查看判定历史
"""
import sys
import os
import json
import argparse
from datetime import datetime

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from master_db import MasterDatabase
from verifier import MasterVerifier
from config import logger

JUDGE_LOG = os.path.join(_THIS_DIR, "child_judgements.jsonl")


def _db():
    return MasterDatabase()


def _verifier(db=None):
    return MasterVerifier(master_db=db or _db())


def cmd_list(args):
    db = _db()
    pend = db.list_pending(limit=500)
    awaiting = [p for p in pend if p.get("status") == "awaiting_child_judge"]
    other = [p for p in pend if p.get("status") in ("pending", "processing")]
    print(f"待判定: {len(awaiting)} 条 | 未挂起: {len(other)} 条")
    print("-" * 100)
    for p in awaiting:
        vs = p.get("verification_summary", {})
        dep = ""
        vr = p.get("verification_result", "")
        # 从 verification_result 提取依赖核对结果
        try:
            vrj = json.loads(vr) if isinstance(vr, str) else {}
            dc = vrj.get("stages", {}).get("dependency_check", {})
            if dc:
                dep = f"依赖: 满足{len(dc.get('satisfied', []))} 缺{len(dc.get('missing', []))} 互锁{len(dc.get('interlock_deps', []))}"
        except Exception:
            pass
        print(
            f"{p['submission_id']} | {p['formula_name'][:45]} | "
            f"berry={vs.get('berry_check', '')} n={vs.get('berry_n_value', 0)} | {dep}"
        )
    print("-" * 100)
    for p in other:
        print(f"  (未挂起) {p['submission_id']} | {p['formula_name'][:40]} | {p.get('status')}")
    return 0


def cmd_show(args):
    db = _db()
    pending = db.get_pending(args.submission_id)
    if not pending:
        print(f"❌ 候选公式不存在: {args.submission_id}")
        return 1
    meta = pending["metadata"]
    print(f"提交ID: {args.submission_id}")
    print(f"公式名: {meta.get('formula_name', '')}")
    print(f"文章编号: {meta.get('article_number', '')}")
    print(f"拓扑分类: {meta.get('topology_class', '')}")
    print(f"状态: {meta.get('status', '')}")
    print(f"提交方: {meta.get('source_agent', '')}")
    ih = meta.get("interlock_hint", "")
    if ih:
        print(f"互锁提示: {ih}")
    vr = meta.get("verification_result", "")
    if vr:
        try:
            vrj = json.loads(vr) if isinstance(vr, str) else vr
            stages = vrj.get("stages", {})
            print("\n===== 机械检查结果 =====")
            bc = stages.get("berry_check", {})
            print(
                f"Berry: 相位={bc.get('berry_phase', 0)} rad | "
                f"n={bc.get('n_value', 0)} | 级别={bc.get('consummation_level', '')} | "
                f"闭合误差={bc.get('closure_error', 0)}"
            )
            fs = stages.get("falsification", {})
            print(f"证伪检查: all_passed={fs.get('all_passed', '')}")
            dc = stages.get("dependency_check", {})
            print("\n===== 依赖核对（程序化） =====")
            print(f"全部满足: {dc.get('all_satisfied', '')}")
            print(f"已满足: {dc.get('satisfied', [])}")
            print(f"缺失: {dc.get('missing', [])}")
            print(f"互锁同批: {dc.get('interlock_deps', [])}")
        except Exception as e:
            print(f"(verification_result 解析失败: {e})")
    print("\n===== 公式内容与推导链 =====")
    print(pending["document"][:6000])
    return 0


def cmd_prepare(args):
    db = _db()
    v = _verifier(db)
    result = v.verify_submission(args.submission_id)
    print(f"action={result.get('action')} | judge_method={result.get('judge_method')}")
    if result.get("stages", {}).get("dependency_check"):
        dc = result["stages"]["dependency_check"]
        print(f"依赖核对: 满足{len(dc.get('satisfied', []))} 缺失{len(dc.get('missing', []))} 互锁{len(dc.get('interlock_deps', []))}")
        if dc.get("missing"):
            print(f"  ⚠ 缺失: {dc['missing']}")
    return 0


def cmd_prepare_all(args):
    db = _db()
    v = _verifier(db)
    pend = db.list_pending(limit=500)
    targets = [p for p in pend if p.get("status") == "pending"]
    if not targets:
        print("没有 pending 公式需要挂起")
        return 0
    print(f"挂起 {len(targets)} 条...")
    for p in targets:
        try:
            result = v.verify_submission(p["submission_id"])
            print(f"  {p['submission_id']} | {p['formula_name'][:40]} → {result.get('action')}")
        except Exception as e:
            print(f"  ❌ {p['submission_id']} | 异常: {e}")
    return 0


def cmd_judge(args):
    db = _db()
    v = _verifier(db)
    if args.verdict not in ("promote", "reject", "dependency_gap"):
        print(f"❌ 未知判定: {args.verdict}（promote / reject / dependency_gap）")
        return 1
    result = v.child_judge(
        submission_id=args.submission_id,
        verdict=args.verdict,
        consummation_level=args.level,
        reason=args.reason,
        judge=args.judge,
    )
    action = result.get("action", "")
    if action == "promoted":
        print(f"✅ 已入库: {result.get('master_id', '')} | 级别: {args.level}")
    elif action == "alternative_proof":
        print(f"✅ 附加为替代证明 → {result.get('attached_to', '')}")
    elif action == "rejected":
        print(f"❌ 已驳回: {result.get('rejection_reason', '')[:120]}")
    elif action == "dependency_gap":
        print(f"⏸ 依赖不足，等待补全")
    else:
        print(f"❓ 结果: {result}")
    return 0


def cmd_rejudge(args):
    """存量真理重新判定（按新判据）：keep=保留 / suspend=标记存疑"""
    db = _db()
    v = _verifier(db)

    # 全量查真理层（含 suspended）
    all_truth = db.master_collection.get(include=["metadatas"])
    target = None
    for mid, meta in zip(all_truth["ids"], all_truth["metadatas"]):
        if str(meta.get("permanent_number", "")) == str(args.permanent_number):
            target = {"master_id": mid, "meta": meta}
            break
    if not target:
        print(f"❌ 真理层无永久编号 #{args.permanent_number}")
        return 1

    name = target["meta"].get("formula_name", "")
    print(f"重新判定: #{args.permanent_number} | {name}")
    print(f"  当前状态: {target['meta'].get('status', 'verified')} | "
          f"原判据: {target['meta'].get('judge_method', 'llm_consummation')}")

    if args.verdict == "keep":
        meta = dict(target["meta"])
        meta["judge_method"] = "child_ai"
        meta["consummation_level"] = args.level or meta.get("consummation_level", "")
        meta["child_judged_at"] = datetime.now().isoformat()
        db._write(db.master_collection, 'update', ids=[target["master_id"]], metadatas=[meta])
        record = {
            "submission_id": target["master_id"],
            "formula_name": name,
            "article_number": meta.get("article_number", ""),
            "permanent_number": str(args.permanent_number),
            "verdict": "keep",
            "consummation_level": args.level or "",
            "reason": args.reason or "存量重新判定通过（新判据）",
            "judge": args.judge,
            "judged_at": datetime.now().isoformat(),
            "rejudge": True,
        }
        v._log_child_judgement(record)
        print(f"✅ 保留: 判定信息已更新（judge_method=child_ai, level={meta['consummation_level']}）")
        return 0
    elif args.verdict == "suspend":
        ok = db.suspend_formula(target["master_id"], args.reason or "存量重新判定未通过（新判据）")
        if ok:
            record = {
                "submission_id": target["master_id"],
                "formula_name": name,
                "article_number": target["meta"].get("article_number", ""),
                "permanent_number": str(args.permanent_number),
                "verdict": "suspend",
                "consummation_level": "",
                "reason": args.reason or "存量重新判定未通过（新判据）",
                "judge": args.judge,
                "judged_at": datetime.now().isoformat(),
                "rejudge": True,
            }
            v._log_child_judgement(record)
            print(f"⏸ 已标记存疑: #{args.permanent_number}（记录保留，退出真理层查询）")
            return 0
        print("❌ 标记存疑失败")
        return 1
    else:
        print("❌ 未知判定: keep / suspend")
        return 1


def cmd_log(args):
    if not os.path.exists(JUDGE_LOG):
        print("判定历史为空")
        return 0
    with open(JUDGE_LOG, encoding="utf-8") as f:
        lines = f.readlines()
    print(f"判定记录: {len(lines)} 条")
    print("-" * 100)
    for line in lines[-30:]:
        try:
            r = json.loads(line)
            tag = "重判" if r.get("rejudge") else "判定"
            print(
                f"[{tag}] {r.get('judged_at', '')[:19]} | "
                f"{r.get('formula_name', '')[:35]} | "
                f"{r.get('verdict', '')} | {r.get('consummation_level', '')} | "
                f"{str(r.get('reason', ''))[:50]}"
            )
        except Exception:
            pass
    return 0


def main():
    parser = argparse.ArgumentParser(description="子AI判定接口（shell + 落盘）")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="列出待判定公式")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="显示完整判定材料")
    p_show.add_argument("submission_id")
    p_show.set_defaults(func=cmd_show)

    p_prep = sub.add_parser("prepare", help="触发挂起（机械检查+依赖核对）")
    p_prep.add_argument("submission_id")
    p_prep.set_defaults(func=cmd_prepare)

    p_prep_all = sub.add_parser("prepare_all", help="所有 pending → 挂起")
    p_prep_all.set_defaults(func=cmd_prepare_all)

    p_judge = sub.add_parser("judge", help="提交判定")
    p_judge.add_argument("submission_id")
    p_judge.add_argument("--verdict", required=True, choices=["promote", "reject", "dependency_gap"])
    p_judge.add_argument("--level", default="", help="圆满级别: 初圆满/中圆满/上圆满")
    p_judge.add_argument("--reason", default="", help="判定理由")
    p_judge.add_argument("--judge", default="child_ai", help="判定人标识")
    p_judge.set_defaults(func=cmd_judge)

    p_rej = sub.add_parser("rejudge", help="存量真理重新判定")
    p_rej.add_argument("permanent_number", help="永久编号（如 145）")
    p_rej.add_argument("--verdict", required=True, choices=["keep", "suspend"])
    p_rej.add_argument("--level", default="", help="圆满级别")
    p_rej.add_argument("--reason", default="", help="判定理由")
    p_rej.add_argument("--judge", default="child_ai")
    p_rej.set_defaults(func=cmd_rejudge)

    p_log = sub.add_parser("log", help="查看判定历史")
    p_log.set_defaults(func=cmd_log)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
