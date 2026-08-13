#!/usr/bin/env python3
"""
定理依赖图构建器 v3
全面扫描文章中的定理声明和依赖关系，构建 DAG。
修复：
- 文章级依赖改为软链接（不生成定理-定理边）
- 同文章内联引用不生成边（避免 Vol-0 根节点消失）
- TOC 匹配收紧到标题行，减少名称噪声
输出: app/data/theorem_dependency_graph.json
"""

import re
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime

ARTICLES_DIR = Path(__file__).parent.parent / "articles"
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "theorem_dependency_graph.json"

SKIP_PATTERNS = [
    r"^00_.*", r"^MOC_.*", r"^Cover_Letter.*", r"^zenodo_.*",
]

def should_skip(filename: str) -> bool:
    for pat in SKIP_PATTERNS:
        if re.match(pat, filename):
            return True
    return False

def parse_article_number(filename: str) -> Optional[str]:
    m = re.match(r"^(\d+\.\d+)_.*", filename)
    return m.group(1) if m else None


# ─── 定理声明提取 ───

def extract_theorem_declarations(content: str, article_num: str) -> List[dict]:
    """
    从文章中提取所有定理声明。支持多种格式：
    1. **定理 X.Y.Z.WW（名称）。** 内容...
    2. **定理 X.Y.Z.WW。** 内容...
    3. **定理 X.Y.Z.WW**。内容...
    4. | 定理 X.Y.Z.WW | 名称 | 状态 |  (定理索引表)
    5. 标题中的: ### §2.4　定理 8.18.8.01：特征加速度
    """
    theorems = []
    seen = set()

    # 格式1-3: bold 声明
    # 匹配 **定理 X.Y.Z.WW ... ** 或 **定理 X.Y.Z.WW ...
    bold_pattern = re.compile(
        r'\*\*(定理|命题|引理|推论|原理)\s*(\d+\.\d+\.\d+\.\d+)(?:[^∗]*?)\*\*'
    )
    for m in bold_pattern.finditer(content):
        ttype = m.group(1)
        tnum = m.group(2)
        if tnum in seen:
            continue
        seen.add(tnum)
        # 提取名称（括号内容）
        ctx = content[m.start():m.end()+80]
        name_match = re.search(r'[（(]([^）)]+)[）)]', ctx)
        name = name_match.group(1) if name_match else ""
        theorems.append({
            "number": tnum,
            "type": ttype,
            "name": name,
            "article": article_num,
            "source": "bold_declaration",
        })

    # 格式4: 定理索引表
    idx_match = re.search(r"## 定理索引\s*\n(.*?)(?=\n## [^#]|\Z)", content, re.DOTALL)
    if idx_match:
        idx_text = idx_match.group(1)
        for line in idx_text.split("\n"):
            line = line.strip()
            if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|", line):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue
            type_num = parts[1]
            statement = parts[2] if len(parts) > 2 else ""
            m = re.match(r"(定理|命题|引理|推论|原理)\s*(\d+\.\d+\.\d+\.\d+)?", type_num)
            if m:
                ttype = m.group(1)
                tnum = m.group(2)
                if tnum and tnum not in seen:
                    seen.add(tnum)
                    theorems.append({
                        "number": tnum,
                        "type": ttype,
                        "name": statement,
                        "article": article_num,
                        "source": "theorem_index_table",
                    })

    # 格式5: 章节目录中的定理声明（仅匹配标题行，减少噪声）
    toc_pattern = re.compile(
        r'^#{2,4}\s+(?:§\S+\s+)?'
        r'(定理|命题|引理|推论)\s*(\d+\.\d+\.\d+\.\d+)[：:]\s*([^\n]{1,120})',
        re.MULTILINE
    )
    for m in toc_pattern.finditer(content):
        ttype = m.group(1)
        tnum = m.group(2)
        name = m.group(3).strip()
        if tnum not in seen:
            seen.add(tnum)
            theorems.append({
                "number": tnum,
                "type": ttype,
                "name": name[:80],
                "article": article_num,
                "source": "toc_heading",
            })

    return theorems


# ─── 依赖关系提取 ───

def extract_dependencies(content: str, article_num: str) -> dict:
    """
    提取依赖关系：
    1. 文章头部: **依赖**: 0.7, 0.8
    2. 文章头部: **前置依赖**：定理 5.1.1.01, ...
    3. 正文中的内联引用: 定理 X.Y.Z.WW
    """
    deps = {
        "article_deps": [],      # 依赖的文章编号（软链接）
        "theorem_deps": [],      # 依赖的定理编号（来自头部）
        "inline_refs": [],       # 正文中引用的定理
    }

    header = content[:3000]

    # 文章级依赖
    m = re.search(r"\*\*依赖\*\*[：:]\s*(.+?)(?:\n|$)", header)
    if m:
        deps["article_deps"] = re.findall(r"(\d+\.\d+)", m.group(1))

    # 定理级前置依赖
    m = re.search(r"\*\*前置依赖\*\*[：:]\s*(.+?)(?:\n|$)", header)
    if m:
        deps["theorem_deps"] = re.findall(
            r"(?:定理|命题|引理|推论)\s*(\d+\.\d+\.\d+\.\d+)", m.group(1)
        )

    # 正文中的内联引用
    inline_pattern = re.compile(r'(定理|命题|引理|推论)\s*(\d+\.\d+\.\d+\.\d+)')
    bold_regions = []
    for m in re.finditer(r'\*\*.*?\*\*', content):
        bold_regions.append((m.start(), m.end()))

    for m in inline_pattern.finditer(content):
        tnum = m.group(2)
        # 跳过 bold 区域内的引用（那是定理声明）
        in_bold = any(start <= m.start() < end for start, end in bold_regions)
        if in_bold:
            continue
        # 跳过定理索引表区域
        idx_start = content.find("## 定理索引")
        if idx_start > 0 and m.start() > idx_start:
            continue
        deps["inline_refs"].append(tnum)

    return deps


# ─── 构建完整图 ───

def build_graph():
    nodes: Dict[str, dict] = {}
    article_info: Dict[str, dict] = {}

    articles = sorted([f for f in os.listdir(ARTICLES_DIR) if f.endswith(".md")])

    # ── 阶段1: 提取所有声明 ──
    for filename in articles:
        if should_skip(filename):
            continue

        article_num = parse_article_number(filename)
        if article_num is None:
            continue

        filepath = ARTICLES_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        vol, ch = article_num.split(".")
        vol = int(vol)

        # 提取定理声明
        theorems = extract_theorem_declarations(content, article_num)
        # 提取依赖
        deps = extract_dependencies(content, article_num)

        # 文章目录归属
        series_map = {
            0: "Vol-0_元基础", 1: "Vol-1_编码框架",
            2: "Vol-2_物理常数导出", 3: "Vol-3_物质场动力学",
            4: "Vol-4_因果场动力学", 5: "Vol-5_信息场动力学",
            6: "Vol-6_三场耦合", 7: "Vol-7_标准模型重建",
            8: "Vol-8_引力与宇宙学", 9: "Vol-9_预言检验",
            10: "Vol-10_应用", 11: "Vol-11_总结与哲学",
        }
        directory = series_map.get(vol, f"Vol-{vol}")

        title = filename.split("_CN_")[0]
        if "_" in title:
            title = title.split("_", 1)[1]

        article_info[article_num] = {
            "filename": filename,
            "title": title,
            "directory": directory,
            "theorem_list": [t["number"] for t in theorems],
            "num_theorems": len(theorems),
            "article_deps": deps["article_deps"],           # 软链接
            "theorem_deps_head": deps["theorem_deps"],      # 硬边
            "inline_refs_unique": list(set(deps["inline_refs"])),
        }

        # 建立节点（先到先得，后处理的文章不覆盖已有声明）
        for thm in theorems:
            tnum = thm["number"]
            if tnum in nodes:
                continue
            nodes[tnum] = {
                "number": tnum,
                "type": thm["type"],
                "name": thm.get("name", ""),
                "statement": thm.get("name", ""),
                "article": article_num,
                "filename": filename,
                "source": thm.get("source", ""),
                "depends_on": [],
                "depended_by": [],
            }

        if theorems:
            print(f"  [{article_num}] {filename}: {len(theorems)} declared")
        else:
            print(f"  [{article_num}] {filename}: (0 declared, {len(deps['inline_refs'])} refs)")

    # ── 阶段2: 建立依赖边 ──

    # 2a. 文章级依赖: 保留为软链接（仅用于前端导航），不生成定理-定理边

    # 2b. 定理级头部依赖: A 的 **前置依赖** 声明的定理
    for article_num, info in article_info.items():
        for dep_thm in info["theorem_deps_head"]:
            if dep_thm in nodes:
                for src_thm in info["theorem_list"]:
                    if src_thm in nodes and src_thm != dep_thm:
                        if dep_thm not in nodes[src_thm]["depends_on"]:
                            nodes[src_thm]["depends_on"].append(dep_thm)
                        if src_thm not in nodes[dep_thm]["depended_by"]:
                            nodes[dep_thm]["depended_by"].append(src_thm)

    # 2c. 内联引用: 正文中引用的定理（仅跨文章，同文章内部引用不生成边）
    for article_num, info in article_info.items():
        for ref_thm in info["inline_refs_unique"]:
            if ref_thm in nodes:
                ref_article = ".".join(ref_thm.split(".")[:2])
                # 跳过同文章内部引用（推导序列自然产生，不进入 DAG）
                if ref_article == article_num:
                    continue
                for src_thm in info["theorem_list"]:
                    if src_thm in nodes and src_thm != ref_thm:
                        if ref_thm not in nodes[src_thm]["depends_on"]:
                            nodes[src_thm]["depends_on"].append(ref_thm)
                        if src_thm not in nodes[ref_thm]["depended_by"]:
                            nodes[ref_thm]["depended_by"].append(src_thm)

    # ── 统计 ──
    total_nodes = len(nodes)
    total_edges = sum(len(n["depends_on"]) for n in nodes.values())

    roots = [tnum for tnum, n in nodes.items() if len(n["depends_on"]) == 0]
    leaves = [tnum for tnum, n in nodes.items() if len(n["depended_by"]) == 0]

    most_cited = sorted(nodes.items(), key=lambda x: len(x[1]["depended_by"]), reverse=True)[:30]

    by_type = defaultdict(int)
    by_volume = defaultdict(int)
    for tnum, n in nodes.items():
        by_type[n["type"]] += 1
        vol = int(tnum.split(".")[0])
        by_volume[str(vol)] += 1

    output = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "total_articles": len(article_info),
            "total_theorems": total_nodes,
            "total_edges": total_edges,
            "roots_count": len(roots),
            "leaves_count": len(leaves),
        },
        "nodes": nodes,
        "articles": article_info,
        "statistics": {
            "most_cited": [
                {
                    "number": tnum, "type": n["type"],
                    "name": n.get("name", ""),
                    "article": n["article"],
                    "cited_by_count": len(n["depended_by"]),
                    "depends_on_count": len(n["depends_on"]),
                } for tnum, n in most_cited
            ],
            "by_type": dict(by_type),
            "by_volume": dict(by_volume),
            "roots": roots[:50],
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"依赖图构建完成")
    print(f"文章数: {len(article_info)}")
    print(f"定理节点: {total_nodes}")
    print(f"依赖边: {total_edges}")
    print(f"根节点 (无依赖): {len(roots)}")
    print(f"叶节点 (无被依赖): {len(leaves)}")
    print(f"类型分布: {dict(by_type)}")
    print(f"输出: {OUTPUT_FILE}")

    print(f"\n最被依赖的定理 Top 15:")
    for i, item in enumerate(output["statistics"]["most_cited"][:15], 1):
        name = item.get("name", "")[:60]
        print(f"  {i:2}. {item['number']} ({item['type']}) [{item['article']}]")
        print(f"      {name}")
        print(f"      被引用 {item['cited_by_count']} 次, 依赖 {item['depends_on_count']} 个")

if __name__ == "__main__":
    build_graph()
