"""
guardian.py — 几何论护法调度器
为大模型提供推导建议、策略推荐和卡点诊断。

功能：
1. 开局注入：推导类问题自动注入定理地图 + 推导策略建议
2. 重复读取检测：连续读同一篇文章多次时提示换方向
3. 临近定理推荐：基于依赖图推荐"一步之遥但还没用到的定理"
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

# ==================== 配置 ====================

_GRAPH_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "theorem_dependency_graph.json"
)

# 推导策略库（与 gap_workbench/templates.py 对齐，但更面向开局建议）
_DERIVATION_STRATEGIES = {
    "NUMERIC": [
        ("闭式变换", "尝试将目标量分解为已知几何常数的组合（如 θ_C, θ_I, Λ_H, δ 等）"),
        ("数值锚定", "对照实验/物理常数（如玻尔半径、PDG值），看数量级和精度是否匹配"),
        ("因子分解", "把目标数值做因子分解，寻找与谱参数/结构常数的对应关系"),
    ],
    "DERIVATION": [
        ("闭式变换", "尝试变量替换（如 u=θ_C+θ_I, v=θ_C−θ_I）、因子分解、化简"),
        ("几何对应", "与已知几何量/定理对应：流、曲率、守恒量、不动点"),
        ("微分/界", "求导找极值、单调性、一致界的解析估计"),
        ("最优参数", "找临界点和最优参数的解析位置（对称性、驻点）"),
    ],
    "PROOF": [
        ("反证法", "假设结论不成立，推导矛盾"),
        ("结构归纳", "从基础情形出发，逐步推广到一般情况"),
        ("对偶映射", "从对偶角度重新表述问题，可能更容易证明"),
        ("维度约化", "降一维看看低维版本是否已知，再反推高维"),
    ],
    "GENERAL": [
        ("依赖链追踪", "沿定理依赖图向前追溯，找到最底层的公理/假设"),
        ("跨文章关联", "查找其他文章中是否有类似结论或可借鉴的方法"),
        ("数值验证", "用具体数值代入检验结论是否成立（calculate_math工具）"),
    ],
}

# 问题类型 → 策略类型映射
_QUERY_TYPE_PATTERNS = {
    "DERIVATION": ["推导", "导出", "得出", "怎么来的", "如何", "机制", "来源"],
    "PROOF": ["证明", "证", "成立", "为什么", "因为", "原因"],
    "NUMERIC": ["数值", "值是", "等于", "多少", "计算", "估算", "精确值"],
}


# ==================== 定理依赖图加载 ====================

class TheoremGraph:
    """定理依赖图的轻量加载器。"""

    def __init__(self, graph_path: str = _GRAPH_FILE):
        self.graph_path = graph_path
        self.nodes = {}          # {thm_number: node_data}
        self.articles = {}       # {article_number: article_info}
        self.article_to_thms = defaultdict(list)  # {article_num: [thm_num, ...]}
        self.loaded = False
        self._load()

    def _load(self):
        if not os.path.exists(self.graph_path):
            logger.warning(f"[GUARDIAN] 定理依赖图不存在: {self.graph_path}")
            return
        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.nodes = data.get("nodes", {})
            self.articles = data.get("articles", {})
            # 建立文章→定理映射
            for tnum, node in self.nodes.items():
                art = node.get("article", "")
                if art:
                    self.article_to_thms[art].append(tnum)
            self.loaded = True
            meta = data.get("meta", {})
            logger.info(
                f"[GUARDIAN] 定理依赖图已加载: "
                f"{meta.get('total_theorems', len(self.nodes))} 个定理, "
                f"{meta.get('total_articles', len(self.articles))} 篇文章"
            )
        except Exception as e:
            logger.error(f"[GUARDIAN] 定理图加载失败: {e}")

    def get_theorems_in_articles(self, article_nums: List[str]) -> List[dict]:
        """获取指定文章中的所有定理。"""
        if not self.loaded:
            return []
        result = []
        for art in article_nums:
            for tnum in self.article_to_thms.get(art, []):
                if tnum in self.nodes:
                    result.append(self.nodes[tnum])
        return result

    def get_neighbor_theorems(
        self,
        known_theorems: List[str],
        direction: str = "both",
        max_results: int = 8
    ) -> List[dict]:
        """
        查找已知定理的"邻居定理"——一步可达但不在已知集合中的。
        direction: "up" (依赖的), "down" (被依赖的), "both"
        """
        if not self.loaded or not known_theorems:
            return []
        known_set = set(known_theorems)
        neighbors = {}  # {thm_num: {count, direction, node}}

        for tnum in known_theorems:
            node = self.nodes.get(tnum)
            if not node:
                continue
            # 上游（依赖的定理）
            if direction in ("up", "both"):
                for dep in node.get("depends_on", []):
                    if dep not in known_set and dep in self.nodes:
                        if dep not in neighbors:
                            neighbors[dep] = {"count": 0, "direction": "up", "node": self.nodes[dep]}
                        neighbors[dep]["count"] += 1
                        if direction == "both":
                            neighbors[dep]["direction"] = "both"
            # 下游（被依赖的定理）
            if direction in ("down", "both"):
                for dep_by in node.get("depended_by", []):
                    if dep_by not in known_set and dep_by in self.nodes:
                        if dep_by not in neighbors:
                            neighbors[dep_by] = {"count": 0, "direction": "down", "node": self.nodes[dep_by]}
                        neighbors[dep_by]["count"] += 1
                        if direction == "both":
                            neighbors[dep_by]["direction"] = "both"

        # 按引用次数排序，返回最多 max_results 个
        sorted_neighbors = sorted(
            neighbors.values(),
            key=lambda x: -x["count"]
        )[:max_results]
        return sorted_neighbors

    def search_theorems_by_keyword(self, keyword: str, max_results: int = 5) -> List[dict]:
        """按关键词搜索定理名称。"""
        if not self.loaded or not keyword:
            return []
        results = []
        kw_lower = keyword.lower()
        for tnum, node in self.nodes.items():
            name = node.get("name", "")
            if kw_lower in name.lower() or keyword in tnum:
                results.append(node)
            if len(results) >= max_results * 3:  # 先多找一些，后面按相关度排
                break
        # 简单排序：名称完全匹配优先，然后是编号匹配
        results.sort(key=lambda n: (
            0 if keyword.lower() in n.get("name", "").lower() else 1,
            -len(n.get("depended_by", []))
        ))
        return results[:max_results]


# 单例
_graph_instance: Optional[TheoremGraph] = None

def get_theorem_graph() -> Optional[TheoremGraph]:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = TheoremGraph()
    return _graph_instance if _graph_instance.loaded else None


# ==================== 问题类型判断 ====================

def classify_query_type(query: str) -> str:
    """判断问题类型，返回 DERIVATION / PROOF / NUMERIC / GENERAL"""
    q = query or ""
    scores = {}
    for qtype, patterns in _QUERY_TYPE_PATTERNS.items():
        scores[qtype] = sum(1 for p in patterns if p in q)
    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
    return "GENERAL"


# ==================== 开局建议生成 ====================

def generate_opening_advice(
    query: str,
    retrieved_articles: List[str],
    vector_kb=None,
    max_strategies: int = 3,
    max_neighbor_theorems: int = 5,
) -> str:
    """
    生成开局护法建议，注入到 system prompt 中。

    参数:
        query: 用户问题
        retrieved_articles: 检索到的文章编号列表（如 ["0.13", "3.2", ...]）
        vector_kb: 向量知识库（暂未使用，预留）
        max_strategies: 最多推荐几条策略
        max_neighbor_theorems: 最多推荐几个临近定理
    """
    sections = []

    # 1. 问题类型 + 策略建议
    qtype = classify_query_type(query)
    strategies = _DERIVATION_STRATEGIES.get(qtype, _DERIVATION_STRATEGIES["GENERAL"])
    strategy_lines = []
    for i, (name, desc) in enumerate(strategies[:max_strategies], 1):
        strategy_lines.append(f"  {i}. 【{name}】{desc}")
    if strategy_lines:
        type_name = {
            "DERIVATION": "推导类",
            "PROOF": "证明类",
            "NUMERIC": "数值类",
            "GENERAL": "综合类",
        }.get(qtype, "综合类")
        sections.append(
            f"【几何护法 · 开局建议】\n"
            f"问题类型：{type_name}\n"
            f"推荐推导策略：\n"
            + "\n".join(strategy_lines)
        )

    # 2. 临近定理推荐（基于依赖图）
    graph = get_theorem_graph()
    if graph and retrieved_articles:
        # 从检索到的文章中提取已知定理
        known_thms = []
        for art in retrieved_articles:
            thms = graph.get_theorems_in_articles([art])
            known_thms.extend(t["number"] for t in thms[:5])  # 每篇取前5个避免过多

        if known_thms:
            # 找下游邻居（可能是推导目标）和上游邻居（可能是基础）
            downstream = graph.get_neighbor_theorems(known_thms, direction="down", max_results=max_neighbor_theorems)
            upstream = graph.get_neighbor_theorems(known_thms, direction="up", max_results=3)

            thm_lines = []
            if downstream:
                thm_lines.append("  下游方向（可能的推导目标）：")
                for item in downstream[:max_neighbor_theorems]:
                    node = item["node"]
                    thm_lines.append(
                        f"    - {node['type']} {node['number']}：{node.get('name', '')[:50]}"
                        f" （被 {item['count']} 个已知定理引用）"
                    )
            if upstream:
                thm_lines.append("  上游方向（可能的基础）：")
                for item in upstream[:3]:
                    node = item["node"]
                    thm_lines.append(
                        f"    - {node['type']} {node['number']}：{node.get('name', '')[:50]}"
                        f" （{item['count']} 个已知定理依赖它）"
                    )
            if thm_lines:
                sections.append(
                    "【几何护法 · 定理导航】\n"
                    f"已检索 {len(retrieved_articles)} 篇文章，涉及 {len(known_thms)} 个定理。\n"
                    "以下是邻近但尚未涉及的定理，可能有用：\n"
                    + "\n".join(thm_lines)
                )

    if not sections:
        return ""

    return "\n\n".join(sections)


# ==================== 重复读取检测 ====================

class ReadTracker:
    """
    追踪工具链中文章的读取模式，检测重复读取。
    用于 stream.py 的工具链循环中。
    """

    def __init__(self, repeat_threshold: int = 3):
        self.repeat_threshold = repeat_threshold  # 同一篇读多少次触发提示
        self.read_count = defaultdict(int)       # {filename: count}
        self.read_history = []                   # 按顺序记录每次读取
        self.last_advice_file = None             # 上次给建议的文件，避免重复提示
        self.total_reads = 0

    def record_read(self, filename: str) -> bool:
        """
        记录一次文件读取。
        返回 True 表示触发了重复读取警告。
        """
        if not filename:
            return False
        self.read_count[filename] += 1
        self.read_history.append(filename)
        self.total_reads += 1

        count = self.read_count[filename]
        # 达到阈值且上次没给过这篇的建议
        if count >= self.repeat_threshold and self.last_advice_file != filename:
            self.last_advice_file = filename
            logger.info(
                f"[GUARDIAN] 重复读取检测触发: {filename} 已读 {count} 次"
            )
            return True
        return False

    def get_repeat_advice(self, filename: str) -> str:
        """
        生成重复读取的护法建议。
        包括：推荐换读的文章（基于引用图）、建议的推导策略。
        """
        count = self.read_count.get(filename, 0)
        lines = [
            f"【几何护法 · 提示】你已读取 {filename} 共 {count} 次。",
            "如果这篇文章没有你需要的答案，建议：",
            "  1. 换用 vector_search 搜索相关关键词，可能其他文章有更直接的论述",
            "  2. 查看该文章引用的其他文章（用 list_articles 按主题浏览）",
            "  3. 尝试不同的推导策略：",
        ]

        # 基于问题类型推荐策略
        # （这里用通用策略，因为不知道具体问题；stream 调用时可传入 query）
        for name, desc in _DERIVATION_STRATEGIES["GENERAL"][:3]:
            lines.append(f"     · {name}：{desc}")

        # 如果有定理图，推荐同主题的其他文章
        graph = get_theorem_graph()
        if graph:
            # 从文件名提取文章编号
            art_match = re.match(r"(\d+\.\d+)", filename)
            if art_match:
                art_num = art_match.group(1)
                art_info = graph.articles.get(art_num)
                if art_info:
                    deps = art_info.get("article_deps", [])
                    if deps:
                        dep_list = ", ".join(deps[:5])
                        lines.append(f"  4. 该文章依赖的其他文章: {dep_list} — 可能包含关键基础")

        lines.append("\n请尝试新的方向，不要反复读取同一篇文章。")
        return "\n".join(lines)

    def get_most_read(self, top_n: int = 3) -> List[Tuple[str, int]]:
        """返回读取次数最多的文件。"""
        return sorted(
            self.read_count.items(),
            key=lambda x: -x[1]
        )[:top_n]


# ==================== 工具函数：从检索结果提取文章编号 ====================

def extract_article_numbers(results: List[dict]) -> List[str]:
    """从向量检索结果中提取文章编号列表。"""
    nums = []
    seen = set()
    for r in results or []:
        meta = r.get("metadata", {})
        fname = meta.get("fname", "")
        if not fname:
            continue
        m = re.match(r"(\d+\.\d+)", fname)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            nums.append(m.group(1))
    return nums


# ==================== 工具函数：检测是否为推导类问题 ====================

_DERIV_PAT = re.compile(
    r'推导|证明|机制|来源|链条|如何|为什么|得出|导出|验证|计算|估算|求值|分析|推演|定理|命题|引理'
)

def is_derivation_query(query: str) -> bool:
    """判断是否为推导类问题（比 server.py 中的更宽泛，用于护法触发）。"""
    if not query:
        return False
    return bool(_DERIV_PAT.search(query))
