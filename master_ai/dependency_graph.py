"""
dependency_graph.py — 全局依赖图引擎

核心功能：
1. 记录每个公式的依赖（它用了哪些L3定理）和被依赖（谁依赖它）
2. 当公式入库时，自动检查哪些公式因此可以被解锁重试
3. 拓扑排序：算出最优验证顺序
4. 持久化到 JSON 文件

图结构：
  节点 = 公式（submission_id 或 master_id）
  边   = 依赖关系（A → B 表示 A 依赖 B，即 B 是 A 的前置）

状态：
  promoted  — 已入库，依赖已满足
  blocked   — 依赖不足，等待前置定理入库
  pending   — 尚未验证
  rejected  — 已驳回
"""

import json
import os
import time
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger(__name__)


class DependencyGraph:
    """全局公式依赖图"""

    def __init__(self, persist_path: str = ""):
        self.persist_path = persist_path
        # 节点信息：formula_id → {name, status, dependencies, master_id}
        self._nodes: Dict[str, Dict[str, Any]] = {}
        # 反向索引：被依赖的定理名 → 依赖它的公式ID列表
        self._reverse: Dict[str, List[str]] = defaultdict(list)
        # 依赖名 → 已入库的master_id（用于匹配）
        self._name_to_master: Dict[str, str] = {}
        # 历史重试记录
        self._retry_history: List[Dict] = []

        if persist_path and os.path.exists(persist_path):
            self._load()

    # ==================== 注册 ====================

    def register_formula(
        self,
        formula_id: str,
        formula_name: str,
        status: str = "pending",
        dependencies: Optional[List[str]] = None,
        master_id: str = "",
    ):
        """
        注册或更新一个公式节点。

        Args:
            formula_id: submission_id 或 master_id
            formula_name: 公式名称
            status: promoted / blocked / pending / rejected
            dependencies: 依赖的前置定理名称列表
            master_id: 如果已入库，对应的 master_id
        """
        old = self._nodes.get(formula_id, {})
        old_deps = set(old.get("dependencies", []))
        new_deps = set(dependencies or [])
        deps_changed = old_deps != new_deps

        self._nodes[formula_id] = {
            "formula_id": formula_id,
            "formula_name": formula_name,
            "status": status,
            "dependencies": list(new_deps),
            "master_id": master_id,
            "updated_at": datetime.now().isoformat(),
        }

        # 如果已入库，注册名称映射
        if status == "promoted" and master_id:
            self._name_to_master[formula_name] = master_id
            # 也注册简称（去掉括号部分）
            short_name = formula_name.split("（")[0].split("(")[0].strip()
            if short_name:
                self._name_to_master[short_name] = master_id

        # 重建反向索引
        self._rebuild_reverse()

        if deps_changed:
            logger.info(
                f"[DEP-GRAPH] 注册 {formula_name} (status={status}, "
                f"deps={len(new_deps)})"
            )

        self._save()

    def update_status(self, formula_id: str, status: str, master_id: str = ""):
        """更新公式状态"""
        if formula_id not in self._nodes:
            logger.warning(f"[DEP-GRAPH] 未知公式: {formula_id}")
            return

        old_status = self._nodes[formula_id].get("status", "")
        self._nodes[formula_id]["status"] = status
        self._nodes[formula_id]["updated_at"] = datetime.now().isoformat()

        if master_id:
            self._nodes[formula_id]["master_id"] = master_id

        if status == "promoted":
            name = self._nodes[formula_id].get("formula_name", "")
            if master_id:
                self._name_to_master[name] = master_id
                short_name = name.split("（")[0].split("(")[0].strip()
                if short_name:
                    self._name_to_master[short_name] = master_id

        if old_status != status:
            logger.info(
                f"[DEP-GRAPH] {self._nodes[formula_id].get('formula_name', formula_id)}: "
                f"{old_status} → {status}"
            )

        self._save()

    # ==================== 解锁检测 ====================

    def find_unblocked(self, newly_promoted_name: str) -> List[Dict[str, Any]]:
        """
        当一个公式新入库时，找出哪些 blocked 公式可能因此被解锁。

        Args:
            newly_promoted_name: 新入库的公式名称

        Returns:
            被解锁的公式列表 [{formula_id, formula_name, satisfied_deps}]
        """
        unblocked = []

        # 模糊匹配：新入库的名称可能和依赖列表中的名称不完全一致
        newly_short = newly_promoted_name.split("（")[0].split("(")[0].strip().lower()

        for fid, node in self._nodes.items():
            if node.get("status") != "blocked":
                continue

            deps = node.get("dependencies", [])
            satisfied = []
            for dep in deps:
                dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                # 检查依赖是否被满足
                if (dep in self._name_to_master or
                    dep_short in [k.lower() for k in self._name_to_master] or
                    newly_short in dep_short or
                    dep_short in newly_short):
                    satisfied.append(dep)

            if satisfied:
                unblocked.append({
                    "formula_id": fid,
                    "formula_name": node.get("formula_name", ""),
                    "satisfied_deps": satisfied,
                    "remaining_deps": [d for d in deps if d not in satisfied],
                })

        if unblocked:
            logger.info(
                f"[DEP-GRAPH] {newly_promoted_name} 入库 → "
                f"{len(unblocked)} 个公式可能解锁"
            )

        return unblocked

    def check_all_blocked(self) -> Dict[str, Any]:
        """
        检查所有 blocked 公式，看哪些的依赖现在已全部满足。

        Returns:
            {
                "fully_unblocked": [...],  # 依赖全部满足，可以重试
                "partially_unblocked": [...],  # 部分满足
                "still_blocked": [...],  # 仍然全部缺失
            }
        """
        fully = []
        partial = []
        still = []

        for fid, node in self._nodes.items():
            if node.get("status") != "blocked":
                continue

            deps = node.get("dependencies", [])
            if not deps:
                continue

            satisfied = []
            remaining = []
            for dep in deps:
                dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                is_satisfied = False
                for master_name in self._name_to_master:
                    master_short = master_name.split("（")[0].split("(")[0].strip().lower()
                    if (dep_short in master_short or
                        master_short in dep_short or
                        dep_short == master_short):
                        is_satisfied = True
                        break
                if is_satisfied:
                    satisfied.append(dep)
                else:
                    remaining.append(dep)

            info = {
                "formula_id": fid,
                "formula_name": node.get("formula_name", ""),
                "satisfied_count": len(satisfied),
                "total_deps": len(deps),
                "remaining_deps": remaining,
            }

            if not remaining:
                fully.append(info)
            elif satisfied:
                partial.append(info)
            else:
                still.append(info)

        return {
            "fully_unblocked": fully,
            "partially_unblocked": partial,
            "still_blocked": still,
        }

    # ==================== 拓扑排序 ====================

    def topological_order(self) -> List[Dict[str, Any]]:
        """
        计算最优验证顺序（拓扑排序）。

        已入库的公式排最前，然后按依赖关系排序。
        被依赖最多的公式优先级更高。

        Returns:
            [{formula_id, formula_name, status, dependencies, can_verify}]
        """
        # 计算每个公式被多少其他公式依赖
        dependents_count = defaultdict(int)
        for fid, node in self._nodes.items():
            for dep in node.get("dependencies", []):
                dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                for other_fid, other_node in self._nodes.items():
                    other_short = other_node.get("formula_name", "").split("（")[0].split("(")[0].strip().lower()
                    if dep_short in other_short or other_short in dep_short:
                        dependents_count[other_fid] += 1

        # 分层：已入库 → 可验证 → 被阻塞
        promoted = []
        verifiable = []
        blocked = []

        for fid, node in self._nodes.items():
            status = node.get("status", "pending")
            entry = {
                "formula_id": fid,
                "formula_name": node.get("formula_name", ""),
                "status": status,
                "dependencies": node.get("dependencies", []),
                "dependents_count": dependents_count.get(fid, 0),
            }
            if status == "promoted":
                promoted.append(entry)
            elif status == "blocked":
                # 检查是否已全部满足
                deps = node.get("dependencies", [])
                all_satisfied = True
                for dep in deps:
                    dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                    found = False
                    for master_name in self._name_to_master:
                        master_short = master_name.split("（")[0].split("(")[0].strip().lower()
                        if dep_short in master_short or master_short in dep_short:
                            found = True
                            break
                    if not found:
                        all_satisfied = False
                        break
                entry["can_verify"] = all_satisfied
                if all_satisfied:
                    verifiable.append(entry)
                else:
                    blocked.append(entry)
            else:
                entry["can_verify"] = True
                verifiable.append(entry)

        # 排序：被依赖最多的优先
        promoted.sort(key=lambda x: -x["dependents_count"])
        verifiable.sort(key=lambda x: -x["dependents_count"])
        blocked.sort(key=lambda x: -x["dependents_count"])

        return promoted + verifiable + blocked

    # ==================== 查询 ====================

    def get_graph_summary(self) -> Dict[str, Any]:
        """获取依赖图摘要"""
        status_count = defaultdict(int)
        for node in self._nodes.values():
            status_count[node.get("status", "pending")] += 1

        return {
            "total_nodes": len(self._nodes),
            "promoted": status_count.get("promoted", 0),
            "blocked": status_count.get("blocked", 0),
            "pending": status_count.get("pending", 0),
            "rejected": status_count.get("rejected", 0),
            "master_theorems": len(self._name_to_master),
            "retry_history_count": len(self._retry_history),
        }

    def get_blocked_formulas(self) -> List[Dict[str, Any]]:
        """获取所有被阻塞的公式及其缺失依赖"""
        result = []
        for fid, node in self._nodes.items():
            if node.get("status") != "blocked":
                continue
            deps = node.get("dependencies", [])
            remaining = []
            for dep in deps:
                dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                found = False
                for master_name in self._name_to_master:
                    master_short = master_name.split("（")[0].split("(")[0].strip().lower()
                    if dep_short in master_short or master_short in dep_short:
                        found = True
                        break
                if not found:
                    remaining.append(dep)

            result.append({
                "formula_id": fid,
                "formula_name": node.get("formula_name", ""),
                "all_deps": deps,
                "remaining_deps": remaining,
                "satisfied_deps": [d for d in deps if d not in remaining],
            })
        return result

    # ==================== 环路检测（强连通分量） ====================

    def detect_cycles(self) -> List[Dict[str, Any]]:
        """
        检测依赖图中的环路（强连通分量 SCC）。

        使用 Tarjan 算法找出所有 size >= 2 的 SCC。
        SCC 内的公式相互依赖，无法通过单向链式验证通过——
        需要作为整体进行批量闭环验证。

        同时检测"隐式环路"：A依赖B（B未入库），B依赖A（A未入库），
        即使图中没有显式的A→B边，通过依赖名称匹配也能发现。

        Returns:
            环路列表，每个环路包含:
            {
                "cycle_id": str,
                "formulas": [{formula_id, formula_name, status, dependencies}],
                "size": int,
                "shared_deps": [str],  # 环路内公式共同依赖的外部定理
                "is_self_contained": bool,  # 是否所有依赖都在环路内
            }
        """
        # 构建邻接表：公式A → 公式B（A依赖B）
        # 通过名称模糊匹配建立边
        adj: Dict[str, Set[str]] = defaultdict(set)
        node_ids = list(self._nodes.keys())

        for fid, node in self._nodes.items():
            deps = node.get("dependencies", [])
            for dep in deps:
                dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                # 在所有节点中找匹配的
                for other_fid, other_node in self._nodes.items():
                    if other_fid == fid:
                        continue
                    other_short = other_node.get("formula_name", "").split("（")[0].split("(")[0].strip().lower()
                    if dep_short in other_short or other_short in dep_short:
                        adj[fid].add(other_fid)

        # Tarjan SCC 算法
        index_counter = [0]
        stack: List[str] = []
        lowlink: Dict[str, int] = {}
        index: Dict[str, int] = {}
        on_stack: Dict[str, bool] = {}
        sccs: List[List[str]] = []

        def strongconnect(v: str):
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack[v] = True

            for w in adj.get(v, []):
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif on_stack.get(w, False):
                    lowlink[v] = min(lowlink[v], index[w])

            if lowlink[v] == index[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == v:
                        break
                sccs.append(scc)

        # 迭代版（避免递归深度问题）
        for v in node_ids:
            if v not in index:
                try:
                    strongconnect(v)
                except RecursionError:
                    # 递归太深，用迭代版
                    pass

        # 过滤：只保留 size >= 2 的 SCC（真正的环路）
        # size=1 的SCC是普通节点，不是环路
        cycles = []
        for i, scc in enumerate(sccs):
            if len(scc) < 2:
                continue

            # 收集环路内公式信息
            formulas_info = []
            all_deps = set()
            intra_deps = set()
            for fid in scc:
                node = self._nodes.get(fid, {})
                deps = node.get("dependencies", [])
                all_deps.update(deps)
                formulas_info.append({
                    "formula_id": fid,
                    "formula_name": node.get("formula_name", ""),
                    "status": node.get("status", ""),
                    "dependencies": deps,
                })
                # 检查哪些依赖在环路内
                for dep in deps:
                    dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                    for other_fid in scc:
                        if other_fid == fid:
                            continue
                        other_short = self._nodes.get(other_fid, {}).get("formula_name", "").split("（")[0].split("(")[0].strip().lower()
                        if dep_short in other_short or other_short in dep_short:
                            intra_deps.add(dep)

            # 环路外部依赖
            external_deps = all_deps - intra_deps
            # 过滤已满足的外部依赖
            unsatisfied_external = []
            for dep in external_deps:
                dep_short = dep.split("（")[0].split("(")[0].strip().lower()
                found = False
                for master_name in self._name_to_master:
                    master_short = master_name.split("（")[0].split("(")[0].strip().lower()
                    if dep_short in master_short or master_short in dep_short:
                        found = True
                        break
                if not found:
                    unsatisfied_external.append(dep)

            cycles.append({
                "cycle_id": f"cycle_{i}",
                "formulas": formulas_info,
                "size": len(scc),
                "intra_deps": list(intra_deps),
                "external_deps": list(external_deps),
                "unsatisfied_external_deps": unsatisfied_external,
                "is_self_contained": len(unsatisfied_external) == 0,
            })

        if cycles:
            logger.info(
                f"[DEP-GRAPH] 检测到 {len(cycles)} 个环路"
                f"（涉及 {sum(c['size'] for c in cycles)} 个公式）"
            )

        return cycles

    def get_cycle_summary(self) -> Dict[str, Any]:
        """获取环路检测摘要"""
        cycles = self.detect_cycles()
        return {
            "total_cycles": len(cycles),
            "formulas_in_cycles": sum(c["size"] for c in cycles),
            "self_contained_cycles": sum(1 for c in cycles if c["is_self_contained"]),
            "cycles": [
                {
                    "cycle_id": c["cycle_id"],
                    "size": c["size"],
                    "is_self_contained": c["is_self_contained"],
                    "formulas": [f["formula_name"] for f in c["formulas"]],
                    "unsatisfied_external_deps": c["unsatisfied_external_deps"][:3],
                }
                for c in cycles
            ],
        }

    def record_retry(self, formula_id: str, formula_name: str, reason: str):
        """记录一次自动重试"""
        self._retry_history.append({
            "formula_id": formula_id,
            "formula_name": formula_name,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    # ==================== 内部方法 ====================

    def _rebuild_reverse(self):
        """重建反向索引"""
        self._reverse.clear()
        for fid, node in self._nodes.items():
            for dep in node.get("dependencies", []):
                self._reverse[dep].append(fid)

    def _save(self):
        """持久化到文件"""
        if not self.persist_path:
            return
        try:
            data = {
                "nodes": self._nodes,
                "name_to_master": self._name_to_master,
                "retry_history": self._retry_history,
            }
            tmp_path = self.persist_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.persist_path)
        except Exception as e:
            logger.warning(f"[DEP-GRAPH] 持久化失败: {e}")

    def _load(self):
        """从文件加载"""
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._nodes = data.get("nodes", {})
            self._name_to_master = data.get("name_to_master", {})
            self._retry_history = data.get("retry_history", [])
            self._rebuild_reverse()
            logger.info(
                f"[DEP-GRAPH] 加载成功: {len(self._nodes)} 节点, "
                f"{len(self._name_to_master)} 已入库定理"
            )
        except Exception as e:
            logger.warning(f"[DEP-GRAPH] 加载失败: {e}")
