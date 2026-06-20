#!/usr/bin/env python3
"""
自动从 70 篇几何论文章中提取关键知识，批量注入教学系统。

用法：
  1. 先启动 geometry_ai_server_v5_12.py
  2. 然后运行本脚本：
     python3 auto_teach.py

提取策略：
  - 每篇文章的标题 + 摘要
  - 所有带编号的定理、命题、引理、推论
  - 所有带编号的公式（$$...$$ 或 $...$ 中含 = 的行）
  - 所有带粗体的定义（**定义** 或 **公理** 开头的段落）
  - 关键常数声明（含数值的行）
"""

import re
import os
import json
import time
import requests

ARTICLES_DIR = "/Users/oygb/AI/articles"
API_BASE = "http://localhost:5000"
BATCH_SIZE = 5  # 每批注入几条，避免过快
DELAY = 0.3     # 每批之间延迟秒数

# 提取规则
def extract_knowledge(filepath: str) -> list:
    """从一篇文章中提取关键知识条目"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    fname = os.path.basename(filepath)
    entries = []

    # 1. 提取标题和摘要
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    abstract_match = re.search(r'##\s*摘\s*要\s*\n(.*?)(?=\n##|\n---)', content, re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        abstract = abstract_match.group(1).strip() if abstract_match else ""
        if abstract:
            entries.append({
                "topic": f"文章概述: {title}",
                "content": f"文章: {fname}\n标题: {title}\n摘要: {abstract}",
                "source": fname
            })

    # 2. 提取编号定理/命题/引理/推论/公理/定义
    theorem_patterns = [
        r'\*\*(定理|命题|引理|推论|公理|定义|猜想|假设|注记|系)\s*[\d\.]*[\d\.]+\s*[^*]*\*\*[^\n]*\n(.*?)(?=\n\*\*|\n#{1,3}\s|\n---|\Z)',
        r'(?:###\s*(?:定理|命题|引理|推论|公理|定义)[\s\d\.]*.*?)(?:\n\n|\n)(.*?)(?=\n###|\n##|\n---|\Z)',
    ]
    for pat in theorem_patterns:
        for m in re.finditer(pat, content, re.DOTALL):
            text = m.group(0).strip()
            # 取前500字符
            if len(text) > 500:
                text = text[:500] + "..."
            # 提取标题作为 topic
            topic_match = re.search(r'\*\*(定理|命题|引理|推论|公理|定义|猜想|假设)[^*]*\*\*', text)
            topic = topic_match.group(0).strip() if topic_match else text[:60]
            entries.append({
                "topic": topic,
                "content": text,
                "source": fname
            })

    # 3. 提取关键公式行（含 = 和希腊字母/下标的行）
    formula_lines = []
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        # LaTeX 公式行：含 $$ 或 $ 且有 = 号
        if ('$$' in line or ('$' in line and '=' in line)) and len(line) > 20:
            # 清理 LaTeX 标记
            clean = line.replace('$$', '').replace('$', '').strip()
            if len(clean) > 15 and any(c in clean for c in '=∑∏∫∂∇√±≈≠≤≥'):
                formula_lines.append(clean)

    # 去重，每篇文章最多取10个公式
    seen = set()
    formulas = []
    for f in formula_lines:
        if f not in seen and len(formulas) < 10:
            seen.add(f)
            formulas.append(f)
    if formulas:
        entries.append({
            "topic": f"关键公式汇总 ({fname})",
            "content": "\n".join(formulas),
            "source": fname
        })

    # 4. 提取常数声明（含具体数值的行）
    constants = []
    const_pattern = r'(?:常数|锁定|取值|等于|约为|约等于|≈|=\s*\d+\.\d+)[^\n]{5,100}'
    for m in re.finditer(const_pattern, content):
        text = m.group(0).strip()
        if re.search(r'\d+\.\d+', text) and len(text) > 10:
            constants.append(text)
    if constants:
        entries.append({
            "topic": f"关键常数 ({fname})",
            "content": "\n".join(constants[:10]),
            "source": fname
        })

    return entries


def inject_patch(topic: str, content: str, source: str) -> bool:
    """调用 API 注入一条知识补丁"""
    try:
        resp = requests.post(
            f"{API_BASE}/v1/teach/patch",
            json={"topic": topic, "content": content, "source": source},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("success", True)
        else:
            print(f"  [FAIL] {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def main():
    # 扫描所有文章
    files = sorted([
        f for f in os.listdir(ARTICLES_DIR)
        if f.endswith('.md') and not f.startswith('目录')
    ])

    print(f"发现 {len(files)} 篇文章")

    total_entries = 0
    total_injected = 0
    batch = []

    for fname in files:
        fpath = os.path.join(ARTICLES_DIR, fname)
        entries = extract_knowledge(fpath)
        total_entries += len(entries)

        for entry in entries:
            batch.append(entry)
            if len(batch) >= BATCH_SIZE:
                # 注入一批
                for item in batch:
                    ok = inject_patch(item["topic"], item["content"], item["source"])
                    if ok:
                        total_injected += 1
                batch = []
                time.sleep(DELAY)

    # 注入剩余
    for item in batch:
        ok = inject_patch(item["topic"], item["content"], item["source"])
        if ok:
            total_injected += 1

    print(f"\n完成！共提取 {total_entries} 条知识，成功注入 {total_injected} 条")

    # 查看统计
    try:
        resp = requests.get(f"{API_BASE}/v1/teach/stats", timeout=5)
        if resp.status_code == 200:
            stats = resp.json()
            print(f"教学系统统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    except:
        pass


if __name__ == "__main__":
    main()
