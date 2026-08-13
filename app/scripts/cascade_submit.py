#!/usr/bin/env python3
"""
级联提交管理器 — 中增量验证的核心工具。

跟踪提交到主库的定理状态，自动检测依赖满足后可以重新提交的 awaiting_child_judge 项。

用法：
    cascade_submit.py track <定理号> --id <提交ID> --deps "T1,T2" [--name "名称"] [--group "互锁组名"]
    cascade_submit.py update <提交ID> --status <状态> [--master-id "#N"]
    cascade_submit.py cascade          # 分析级联：哪些可以重试
    cascade_submit.py list             # 列出所有提交记录
    cascade_submit.py status           # 概览统计
    cascade_submit.py forget <提交ID>  # 删除一条记录

状态（对应主库 check_master_status 返回值）：
    pending              — 刚提交，尚未查询
    promoted             — 已通过，入库真理层
    awaiting_child_judge — 逻辑通顺，但前置定理未入库
    rejected             — 推导有误，驳回

级联提交流程：
    1. 底层定理提交 → track
    2. check_master_status → update
    3. 上层定理提交（可能 awaiting_child_judge）→ track
    4. 底层定理通过后 → cascade 检查 → 自动标出可重试项
    5. 重新 submit_to_master 可重试项 → 更新为新提交 ID
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# ─── 配置 ─────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
TRACKER_FILE = DATA_DIR / "submission_tracker.json"
TZ = timezone(timedelta(hours=8))  # Asia/Shanghai

VALID_STATUSES = {"pending", "promoted", "awaiting_child_judge", "rejected"}

# ─── 数据加载/保存 ─────────────────────────────────────

def load():
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"submissions": [], "meta": {"created": now_iso()}}

def save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    if "meta" not in data:
        data["meta"] = {"created": now_iso()}
    data["meta"]["updated"] = now_iso()
    data["meta"]["count"] = len(data["submissions"])
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_iso():
    return datetime.now(TZ).isoformat()

# ─── 查找 ──────────────────────────────────────────────

def find_sub(data, sub_id):
    """按提交ID查找（支持前缀匹配）"""
    matches = [s for s in data["submissions"] if s["id"].startswith(sub_id)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"⚠️  多个匹配: {[s['id'] for s in matches]}")
        return None
    return None

def by_theorem(data):
    """按定理号分组"""
    groups = defaultdict(list)
    for s in data["submissions"]:
        groups[s["theorem"]].append(s)
    return dict(groups)

# ─── 命令实现 ──────────────────────────────────────────

def cmd_track(args):
    """track <theorem> --id <sub_id> --deps "T1,T2" [--name "..."] [--group "..."]"""
    if len(args) < 1:
        die("用法: cascade_submit.py track <定理号> --id <提交ID> --deps \"T1,T2\" [--name \"名称\"] [--group \"互锁组\"]")

    theorem = args[0]
    sub_id = pop_flag(args, "--id")
    deps_raw = pop_flag(args, "--deps")
    name = pop_flag(args, "--name") or theorem
    group = pop_flag(args, "--group") or None

    if not sub_id:
        die("缺少 --id <提交ID>")
    if deps_raw is None:
        die("缺少 --deps \"T1,T2,...\"")

    deps = [d.strip() for d in deps_raw.replace("，", ",").split(",") if d.strip()]

    data = load()
    if find_sub(data, sub_id):
        die(f"提交ID '{sub_id}' 已存在，用 update 更新状态")

    entry = {
        "id": sub_id,
        "theorem": theorem,
        "name": name,
        "depends_on": deps,
        "interlock_group": group,
        "status": "pending",
        "master_id": None,
        "submitted_at": now_iso(),
        "last_checked": None,
        "retry_count": 0,
        "history": [{"status": "pending", "at": now_iso()}]
    }

    data["submissions"].append(entry)
    save(data)
    print(f"✅ 已记录: {theorem} ({name}) → ID={sub_id}")
    print(f"   依赖: {', '.join(deps)}")
    if group:
        print(f"   互锁组: {group}")
    print(f"   状态: pending → 请用 check_master_status {sub_id} 查询")


def cmd_update(args):
    """update <sub_id> --status <状态> [--master-id "#N"]"""
    if len(args) < 1:
        die("用法: cascade_submit.py update <提交ID> --status <状态> [--master-id \"#N\"]")

    sub_id = args[0]
    new_status = pop_flag(args, "--status")
    master_id = pop_flag(args, "--master-id")

    if not new_status:
        die("缺少 --status (pending|promoted|awaiting_child_judge|rejected)")
    if new_status not in VALID_STATUSES:
        die(f"无效状态 '{new_status}'，允许: {', '.join(sorted(VALID_STATUSES))}")

    data = load()
    sub = find_sub(data, sub_id)
    if not sub:
        die(f"未找到提交记录: {sub_id}")

    old_status = sub["status"]
    sub["status"] = new_status
    sub["last_checked"] = now_iso()
    if master_id:
        sub["master_id"] = master_id
    sub["history"].append({"status": new_status, "at": now_iso()})
    save(data)

    emoji = {"promoted": "🎉", "awaiting_child_judge": "⏳", "rejected": "❌", "pending": "⏳"}
    print(f"{emoji.get(new_status, '')} {sub['theorem']} ({sub['name']}) : {old_status} → {new_status}")
    if new_status == "awaiting_child_judge":
        print(f"   前置依赖尚未入库，等依赖通过后可重新提交")
    elif new_status == "rejected":
        print(f"   推导有误，修正后可重新提交")


def cmd_cascade(args):
    """cascade — 分析级联状态，标出可重试的 awaiting_child_judge"""

    data = load()
    if not data["submissions"]:
        print("📭 无提交记录")
        return

    subs = data["submissions"]

    # 收集所有已通过的定理
    promoted_theorems = set()
    for s in subs:
        if s["status"] == "promoted":
            promoted_theorems.add(s["theorem"])

    # 分类
    awaiting = [s for s in subs if s["status"] == "awaiting_child_judge"]
    rejected = [s for s in subs if s["status"] == "rejected"]
    pending = [s for s in subs if s["status"] == "pending"]
    promoted_list = [s for s in subs if s["status"] == "promoted"]

    # 分析每个 awaiting_child_judge 的依赖满足情况
    ready = []
    not_ready = []
    for s in awaiting:
        unmet = [d for d in s["depends_on"] if d not in promoted_theorems]
        if not unmet:
            ready.append(s)
        else:
            not_ready.append((s, unmet))

    # ── 输出报告 ──
    print("=" * 60)
    print("  级联提交状态报告")
    print("=" * 60)

    print(f"\n📊 概览: {len(subs)} 条提交记录")
    print(f"   🎉 已通过:    {len(promoted_list)}")
    print(f"   ⏳ 等前置:    {len(awaiting)}")
    print(f"   ❌ 驳回:      {len(rejected)}")
    print(f"   ⏳ 待查询:    {len(pending)}")

    if ready:
        print(f"\n{'='*60}")
        print(f"  🔥 可重试 ({len(ready)}): 依赖已全部满足！")
        print(f"{'='*60}")
        for s in ready:
            deps_str = ", ".join(s["depends_on"])
            retry_n = s["retry_count"] + 1
            print(f"\n  定理: {s['theorem']} ({s['name']})")
            print(f"  提交ID: {s['id']}")
            print(f"  依赖: {deps_str} → 全部已入库 ✓")
            print(f"  操作: submit_to_master(…)  ← 第{retry_n}次提交")
            if s.get("interlock_group"):
                print(f"  ⚠️  互锁组: {s['interlock_group']}（请整组提交）")

    if not_ready:
        print(f"\n{'='*60}")
        print(f"  ⏳ 等待中 ({len(not_ready)}): 依赖尚未全部通过")
        print(f"{'='*60}")
        for s, unmet in not_ready:
            satisfied = [d for d in s["depends_on"] if d in promoted_theorems]
            print(f"\n  定理: {s['theorem']} ({s['name']})")
            print(f"  ✓ 已满足: {', '.join(satisfied) if satisfied else '(无)'}")
            print(f"  ✗ 未满足: {', '.join(unmet)}")
            if s.get("interlock_group"):
                print(f"  🔗 互锁组: {s['interlock_group']}")

    if not awaiting:
        print(f"\n✅ 无待处理的 awaiting_child_judge 项")

    # 待查询的 pending 项
    if pending:
        print(f"\n{'='*60}")
        print(f"  ⏳ 待查询 ({len(pending)}): 尚未获得主库验证结果")
        print(f"{'='*60}")
        for s in pending:
            print(f"\n  定理: {s['theorem']} ({s['name']})")
            print(f"  提交ID: {s['id']}")
            deps_str = ", ".join(s["depends_on"]) if s["depends_on"] else "(根节点)"
            print(f"  依赖: {deps_str}")
            print(f"  操作: check_master_status {s['id']}")

    # 未入库依赖提示
    all_deps = set()
    for s in awaiting:
        all_deps.update(s["depends_on"])
    unknown_deps = all_deps - promoted_theorems - {s["theorem"] for s in subs}

    if unknown_deps:
        print(f"\n{'='*60}")
        print(f"  ⚠️  未知依赖 ({len(unknown_deps)}): 未在提交记录中，也未通过")
        print(f"{'='*60}")
        print(f"  这些定理尚未提交到主库，或未记录在 tracker 中：")
        for d in sorted(unknown_deps):
            print(f"    - {d}")
        print(f"  可能需要先提交这些定理，或用 track 记录已有提交")


def cmd_list(args):
    """list — 列出所有提交记录"""
    data = load()
    if not data["submissions"]:
        print("📭 无提交记录")
        return

    print(f"{'定理':<16} {'名称':<22} {'状态':<24} {'提交ID':<14} {'依赖':<30}")
    print("-" * 110)
    for s in data["submissions"]:
        status_icon = {"promoted": "🎉", "awaiting_child_judge": "⏳", "rejected": "❌", "pending": "⏳"}
        icon = status_icon.get(s["status"], "  ")
        deps = ",".join(s["depends_on"][:3])
        if len(s["depends_on"]) > 3:
            deps += f"…(+{len(s['depends_on'])-3})"
        short_id = s["id"][:12]
        print(f"{s['theorem']:<16} {s['name']:<22} {icon} {s['status']:<22} {short_id:<14} {deps:<30}")


def cmd_status(args):
    """status — 概览统计"""
    data = load()
    subs = data["submissions"]
    if not subs:
        print("📭 无提交记录")
        return

    by_stat = defaultdict(list)
    for s in subs:
        by_stat[s["status"]].append(s)

    print("=" * 50)
    print("  提交状态概览")
    print("=" * 50)
    print(f"  总提交数: {len(subs)}")
    print(f"  🎉 已通过: {len(by_stat.get('promoted', []))}")
    print(f"  ⏳ 待前置: {len(by_stat.get('awaiting_child_judge', []))}")
    print(f"  ❌ 驳回:   {len(by_stat.get('rejected', []))}")
    print(f"  ⏳ 待查询: {len(by_stat.get('pending', []))}")

    # 互锁组统计
    groups = defaultdict(list)
    for s in subs:
        if s.get("interlock_group"):
            groups[s["interlock_group"]].append(s)
    if groups:
        print(f"\n  互锁组:")
        for gname, members in groups.items():
            done = sum(1 for m in members if m["status"] == "promoted")
            print(f"    {gname}: {done}/{len(members)} 已通过")

    # 最近提交
    recent = sorted(subs, key=lambda s: s.get("submitted_at", ""), reverse=True)[:5]
    if recent:
        print(f"\n  最近提交:")
        for s in recent:
            print(f"    {s['theorem']} ({s['name']}) — {s['status']} — {s.get('submitted_at', '?')[:16]}")


def cmd_forget(args):
    """forget <sub_id> — 删除一条提交记录"""
    if len(args) < 1:
        die("用法: cascade_submit.py forget <提交ID>")

    sub_id = args[0]
    data = load()
    sub = find_sub(data, sub_id)
    if not sub:
        die(f"未找到: {sub_id}")

    data["submissions"] = [s for s in data["submissions"] if s["id"] != sub["id"]]
    save(data)
    print(f"🗑️  已删除: {sub['theorem']} ({sub['name']}) — {sub['id']}")


# ─── 工具函数 ──────────────────────────────────────────

def pop_flag(args, flag):
    """从参数列表中提取 --flag value"""
    try:
        idx = args.index(flag)
        val = args[idx + 1]
        del args[idx:idx + 2]
        return val
    except (ValueError, IndexError):
        return None

def die(msg):
    print(f"❌ {msg}")
    sys.exit(1)


# ─── 主入口 ────────────────────────────────────────────

COMMANDS = {
    "track":   (cmd_track,   "记录一次主库提交"),
    "update":  (cmd_update,  "更新提交状态"),
    "cascade": (cmd_cascade, "分析级联：哪些可重试"),
    "list":    (cmd_list,    "列出所有提交记录"),
    "status":  (cmd_status,  "概览统计"),
    "forget":  (cmd_forget,  "删除一条记录"),
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("级联提交管理器 — 中增量验证")
        print()
        for name, (_, desc) in COMMANDS.items():
            print(f"  {name:<10} {desc}")
        print()
        print("状态: pending | promoted | awaiting_child_judge | rejected")
        print("数据: app/data/submission_tracker.json")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        die(f"未知命令: {cmd}\n可用: {', '.join(COMMANDS.keys())}")

    func, _ = COMMANDS[cmd]
    func(sys.argv[2:])


if __name__ == "__main__":
    main()
