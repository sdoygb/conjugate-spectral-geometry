#!/usr/bin/env python3
"""
预提交检查 —— 提交主库前的三道本地预检。

用法:
  python3 app/scripts/pre_submit_check.py deps T1 T2 T3 ...
      检查依赖定理是否在本地图中存在

  python3 app/scripts/pre_submit_check.py cycle NEW_T --deps T1 T2 T3 ...
      检查新定理是否会引入循环依赖 / 依赖间是否存在互锁

  python3 app/scripts/pre_submit_check.py full NEW_T --name "名称" --deps T1 T2 ... [--topology A0|A1] [--berry 0] [--n 1]
      完整预检：依赖存在性 + 互锁检查 + 提交建议

三道预检：
  ① 依赖完整性 — 所有前置定理在本地图中存在（再手动用 search_master_truth 确认主库状态）
  ② 互锁检查   — 依赖之间是否存在互锁（需批量提交）
  ③ 代数验证   — 用 symbolic_verify.py 独立验证关键代数步骤
"""

import json
import sys
import os
from collections import deque
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "data" / "theorem_dependency_graph.json"


def load_graph():
    if not GRAPH_PATH.exists():
        print(f"错误: 定理依赖图不存在 ({GRAPH_PATH})")
        print("请先运行: python3 app/scripts/build_theorem_graph.py")
        sys.exit(1)
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_node(n):
    """格式化节点信息为一行"""
    return f"{n.get('type','?')} {n['number']} — {n.get('name','?')[:50]} [{n.get('article','?')}]"


# ─── ① 依赖完整性 ───────────────────────────────────────────

def check_deps(graph, dep_numbers):
    """检查依赖在本地图中的存在性和状态。"""
    nodes = graph["nodes"]
    results = []
    all_found = True

    for tnum in dep_numbers:
        tnum = tnum.strip()
        if tnum in nodes:
            node = nodes[tnum]
            results.append({
                "number": tnum,
                "status": "found",
                "name": node.get("name", "?"),
                "type": node.get("type", "?"),
                "article": node.get("article", "?"),
                "depends_count": len(node.get("depends_on", [])),
                "cited_by_count": len(node.get("depended_by", [])),
                "is_root": len(node.get("depends_on", [])) == 0
            })
        else:
            results.append({"number": tnum, "status": "not_found"})
            all_found = False

    return results, all_found


def render_deps(results):
    """渲染依赖检查结果。"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ① 依赖完整性检查                                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    need_master = []

    for r in results:
        if r["status"] == "found":
            root_mark = " ★根" if r["is_root"] else ""
            print(f"  ✓ {r['number']}{root_mark}")
            print(f"      {r['type']} — {r['name']}  [{r['article']}]")
            print(f"      本地: 依赖 {r['depends_count']} 条, 被 {r['cited_by_count']} 条引用")
            need_master.append(r["number"])
        else:
            print(f"  ✗ {r['number']}  —— 本地图中未找到！")
            print(f"      请检查定理编号是否正确，或重新扫描文章库。")

    print()

    if all(r["status"] == "found" for r in results):
        print(f"  ✅ 全部 {len(results)} 条依赖在本地图中存在")
        print(f"  ⚠️  下一步: 用 search_master_truth 确认主库状态:")
        print(f"     search_master_truth \"#{' #'.join(need_master)}\"")
    else:
        missing = [r["number"] for r in results if r["status"] == "not_found"]
        print(f"  ❌ {len(missing)} 条依赖未在本地图中: {', '.join(missing)}")

    return all(r["status"] == "found" for r in results)


# ─── ② 互锁检查 ─────────────────────────────────────────────

def find_interlocks(graph, dep_numbers):
    """
    检查依赖之间是否存在互锁（互相可达）。
    
    互锁 = A 的祖先包含 B，且 B 的祖先包含 A。
    如果存在互锁，这些定理必须批量提交到主库（设置 interlock_hint）。
    """
    nodes = graph["nodes"]
    
    # 为每个依赖计算祖先集合
    ancestors = {}
    for tnum in dep_numbers:
        if tnum not in nodes:
            continue
        visited = set()
        queue = deque([tnum])
        while queue:
            cur = queue.popleft()
            if cur in visited:
                continue
            visited.add(cur)
            for parent in nodes.get(cur, {}).get("depends_on", []):
                if parent not in visited:
                    queue.append(parent)
        ancestors[tnum] = visited

    # 检查两两互相可达
    interlocks = []
    deps_list = [d for d in dep_numbers if d in nodes]
    
    for i in range(len(deps_list)):
        for j in range(i + 1, len(deps_list)):
            a, b = deps_list[i], deps_list[j]
            a_reaches_b = b in ancestors.get(a, set())
            b_reaches_a = a in ancestors.get(b, set())
            if a_reaches_b and b_reaches_a:
                interlocks.append((a, b))

    return interlocks


def check_cycle(graph, new_theorem, dep_numbers):
    """检查新定理是否引入循环依赖，以及依赖间互锁情况。"""
    nodes = graph["nodes"]
    report = {"has_cycle": False, "interlocks": [], "warnings": []}

    # 1. 检查依赖间互锁
    interlocks = find_interlocks(graph, dep_numbers)
    if interlocks:
        report["interlocks"] = interlocks
        report["has_cycle"] = True

    # 2. 检查新定理号的直接祖先中是否有人已经依赖了新定理号
    #    （如果新定理号已经在图中存在，检查会不会产生循环）
    if new_theorem in nodes:
        existing = nodes[new_theorem]
        for dep in dep_numbers:
            # 已存在的 new_theorem 是否已经在 dep 的祖先链中？
            if dep in nodes:
                # BFS 从 dep 出发看是否到达 new_theorem
                visited = set()
                queue = deque(nodes[dep].get("depends_on", []))
                while queue:
                    cur = queue.popleft()
                    if cur in visited:
                        continue
                    if cur == new_theorem:
                        report["warnings"].append(
                            f"循环! {dep} 的祖先包含 {new_theorem}，同时 {new_theorem} 也依赖 {dep}"
                        )
                        report["has_cycle"] = True
                        break
                    visited.add(cur)
                    cn = nodes.get(cur)
                    if cn:
                        queue.extend(cn.get("depends_on", []))

    return report


def render_cycle(report, dep_numbers):
    """渲染互锁检查结果。"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ② 互锁检查                                             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    if report["interlocks"]:
        print("  ⚠️  检测到互锁依赖对（互相可达）：")
        for a, b in report["interlocks"]:
            print(f"      {a} ⇄ {b}")
        print()
        print(f"  互锁组必须作为整体提交到主库。")
        print(f"  💡 如果这些依赖已全部在主库真理层中（promoted），则可忽略此警告。")
        print(f"  提交时请设置 interlock_hint 包含这些定理:")
        all_locked = set()
        for a, b in report["interlocks"]:
            all_locked.add(a)
            all_locked.add(b)
        print(f"    interlock_hint: {sorted(all_locked)}")
        print()

    if report["warnings"]:
        print("  ❌ 循环警告:")
        for w in report["warnings"]:
            print(f"      {w}")
        print()

    if not report["interlocks"] and not report["warnings"]:
        print(f"  ✅ 无互锁 — {len(dep_numbers)} 条依赖形成标准树/森林结构")
        print(f"     可单独提交，无需设置 interlock_hint")

    # 仅 warnings（真正的循环）阻塞提交；interlocks 只是提醒设置 interlock_hint
    return not bool(report["warnings"])


# ─── 完整预检 ───────────────────────────────────────────────

def full_check(graph, args):
    """运行完整预检并输出提交建议。"""
    new_theorem = args.get("theorem")
    name = args.get("name", "(未命名)")
    dep_numbers = args.get("deps", [])
    topology = args.get("topology", "A0")
    berry = args.get("berry", 0)
    n_value = args.get("n", 1)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  预提交检查报告                                         ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  定理: {new_theorem}")
    print(f"║  名称: {name}")
    print(f"║  拓扑类: {topology}  |  Berry: {berry}  |  n: {n_value}")
    print(f"║  依赖: {', '.join(dep_numbers) if dep_numbers else '(根节点)'}")
    print("╚══════════════════════════════════════════════════════════╝")

    all_pass = True

    # ① 依赖完整性
    if dep_numbers:
        results, deps_ok = check_deps(graph, dep_numbers)
        render_deps(results)
    else:
        print()
        print("  ① 依赖完整性: 根节点，无依赖 — 跳过")
        deps_ok = True

    if not deps_ok:
        all_pass = False

    # ② 互锁检查
    if dep_numbers:
        report = check_cycle(graph, new_theorem, dep_numbers)
        cycle_ok = render_cycle(report, dep_numbers)
        if not cycle_ok:
            all_pass = False
    else:
        print()
        print("  ② 互锁检查: 根节点 — 跳过")
        cycle_ok = True

    # ③ 代数验证提示
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ③ 代数验证（需手动执行）                               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print("  请对推导中的关键代数步骤运行 symbolic_verify.py：")
    print()
    print("    # 等式验证")
    print("    python3 app/scripts/symbolic_verify.py eq \"lhs\" \"rhs\"")
    print()
    print("    # 数值代入")
    print("    python3 app/scripts/symbolic_verify.py num \"expr\" --subs '{...}' --expected N")
    print()
    print("    # 质量公式（一键）")
    print("    python3 app/scripts/symbolic_verify.py mass --C 839.76 --theta 57.93 --expected 511.0 --unit keV")
    print()

    # 总结
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  总结                                                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    checks = [
        ("① 依赖完整性", deps_ok),
        ("② 互锁检查", cycle_ok),
        ("③ 代数验证", "手动"),
    ]

    for name, status in checks:
        if status == True:
            print(f"  ✅ {name} — 通过")
        elif status == "手动":
            print(f"  ⚡ {name} — 待手动执行")
        else:
            print(f"  ❌ {name} — 未通过")

    print()

    if all_pass:
        print("  🚀 本地预检全部通过！下一步：")
        print()
        if dep_numbers:
            print(f"  1. 确认主库状态: search_master_truth \"#{' #'.join(dep_numbers)}\"")
        print(f"  2. 执行代数验证: symbolic_verify.py ...")
        print(f"  3. 提交到主库: submit_to_master(")
        print(f"       formula_name=\"{new_theorem}：{name}\",")
        print(f"       topology_class=\"{topology}\",")
        print(f"       local_berry_phase={berry},")
        print(f"       local_n_value={n_value}")
        print(f"     )")
        if report.get("interlocks"):
            all_locked = set()
            for a, b in report["interlocks"]:
                all_locked.add(a)
                all_locked.add(b)
            print(f"     ⚠️  记得设置 interlock_hint: {sorted(all_locked)}")
    else:
        print("  ⛔ 预检未通过，请先修复以上问题再提交。")

    print()
    return all_pass


# ─── CLI 入口 ────────────────────────────────────────────────

def parse_full_args(argv):
    """解析 full 子命令的参数。"""
    args = {"deps": [], "topology": "A0", "berry": 0, "n": 1}
    
    i = 2  # 跳过脚本名和 "full"
    while i < len(argv):
        if argv[i] == "--name" and i + 1 < len(argv):
            args["name"] = argv[i + 1]
            i += 2
        elif argv[i] == "--deps" and i + 1 < len(argv):
            # --deps 后面跟逗号分隔的定理列表
            deps_str = argv[i + 1]
            args["deps"] = [d.strip() for d in deps_str.split(",") if d.strip()]
            i += 2
        elif argv[i] == "--topology" and i + 1 < len(argv):
            args["topology"] = argv[i + 1]
            i += 2
        elif argv[i] == "--berry" and i + 1 < len(argv):
            args["berry"] = float(argv[i + 1])
            i += 2
        elif argv[i] == "--n" and i + 1 < len(argv):
            args["n"] = int(argv[i + 1])
            i += 2
        elif i == 2 and not argv[i].startswith("--"):
            # 第一个非选项参数 = 定理编号
            args["theorem"] = argv[i]
            i += 1
        else:
            i += 1
    
    return args


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    graph = load_graph()

    if cmd == "deps":
        dep_numbers = sys.argv[2:]
        if not dep_numbers:
            print("用法: pre_submit_check.py deps T1 T2 T3 ...")
            sys.exit(1)
        results, ok = check_deps(graph, dep_numbers)
        render_deps(results)
        sys.exit(0 if ok else 1)

    elif cmd == "cycle":
        # 用法: pre_submit_check.py cycle NEW_T --deps T1,T2,T3
        if "--deps" not in sys.argv:
            print("用法: pre_submit_check.py cycle NEW_T --deps T1,T2,T3")
            sys.exit(1)
        deps_idx = sys.argv.index("--deps")
        new_theorem = sys.argv[2]
        deps_str = sys.argv[deps_idx + 1] if deps_idx + 1 < len(sys.argv) else ""
        dep_numbers = [d.strip() for d in deps_str.split(",") if d.strip()]
        
        report = check_cycle(graph, new_theorem, dep_numbers)
        ok = render_cycle(report, dep_numbers)
        sys.exit(0 if ok else 1)

    elif cmd == "full":
        args = parse_full_args(sys.argv)
        if "theorem" not in args:
            print("用法: pre_submit_check.py full 定理编号 --name \"名称\" --deps T1,T2,T3 ...")
            sys.exit(1)
        ok = full_check(graph, args)
        sys.exit(0 if ok else 1)

    else:
        print(f"未知子命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
