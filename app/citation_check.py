"""
citation_check.py - 引用来源硬校验

目标：杜绝"幻觉引用"（模型在推导/回答中引用不存在的文章编号或定理）。
原理：
1. 以 articles 目录的真实文件名编号为权威真相源（不依赖向量库，避免"向量库≠原文"）。
2. 从回答文本中提取"文章 X.Y"式的引用标注。
3. 与真实编号集合比对，返回所有不存在的"幻觉引用"列表。

调用方：server.py 质量门控中引用校验；prompts.py 提供引用纪律提示。
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

_ARTICLE_NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)_")

# 引用前缀：紧跟"文章"/"文号"等词之后出现编号，才认定为文章引用（避免误伤 eta、数值等）
_CITE_PREFIX_RE = re.compile(
    r"(?:文章|文号|文\s*#|引用来源|参考文章|依据文章|见\s*文章|如\s*文章)"
    r"\s*(?:[：:\-—_])?\s*([0-9]+(?:\.[0-9]+)*)",
    re.IGNORECASE,
)
# 方括号引用：["文章 0.8"] / [文章0.8] / [0.8]
_CITE_BRACKET_RE = re.compile(
    r"\[(?:文章|文号)?\s*(?:文章|文号)?\s*([0-9]+\.[0-9]+)\]",
    re.IGNORECASE,
)


def load_real_article_ids(articles_dir: str) -> set:
    """扫描文章目录，返回真实存在的文章编号集合（权威真相源）。"""
    ids = set()
    if not articles_dir or not os.path.isdir(articles_dir):
        return ids
    for fname in os.listdir(articles_dir):
        if not fname.lower().endswith((".md", ".txt", ".tex", ".py")):
            continue
        m = _ARTICLE_NUM_RE.match(fname)
        if m:
            ids.add(m.group(1))
    return ids


def extract_citations(text: str) -> list:
    """从回答文本中提取所有疑似文章引用的编号。返回 [(编号, 来源上下文)]。"""
    if not text:
        return []
    cites = []
    for m in _CITE_PREFIX_RE.finditer(text):
        cites.append((m.group(1), text[max(0, m.start() - 15):m.end() + 8]))
    for m in _CITE_BRACKET_RE.finditer(text):
        if not any(c[0] == m.group(1) for c in cites):
            cites.append((m.group(1), text[max(0, m.start() - 15):m.end() + 8]))
    return cites


def verify_citations(text: str, real_article_ids: set) -> dict:
    """
    校验回答中的引用是否真实存在。
    返回: {"ok": bool, "bad": [(编号,上下文)], "cited": [(编号,上下文)]}
    """
    result = {"ok": True, "bad": [], "cited": []}
    if not text:
        return result
    cited = extract_citations(text)
    if not cited:
        return result
    result["cited"] = cited
    bad = []
    for cid, ctx in cited:
        # 前缀精确匹配：引用的编号必须在真实集合中，或它的某个父级前缀在其中
        if cid in real_article_ids:
            continue
        # 细粒度编号（如 5.6.3）回退到父级（如 5.6 / 5）是否真实存在
        parts = cid.split(".")
        prefix_ok = False
        for i in range(len(parts) - 1, 0, -1):
            parent = ".".join(parts[:i])
            if parent in real_article_ids:
                prefix_ok = True
                break
        if not prefix_ok:
            bad.append((cid, ctx.strip()))
    if bad:
        result["ok"] = False
        result["bad"] = bad
    return result


def format_bad_citations(bad) -> str:
    """把幻觉引用格式化为给模型的重写指令。"""
    if not bad:
        return ""
    lines = ["你的回答中引用了以下【不存在的文章编号】："]
    for cid, ctx in bad:
        lines.append(f"  - 文章 {cid}（出现在：…{ctx}…）")
    lines.append(
        "这些编号在文章库中不存在，属于幻觉引用。请重新回答："
        "只引用确认存在、且你能从参考资料或工具查询中证实的文章编号；"
        "若不确定某编号是否存在，先用 vector_search / list_articles 核实，找不到就删除该引用或改为匹配的真实编号。"
    )
    return "\n".join(lines)