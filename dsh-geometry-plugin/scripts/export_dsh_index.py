#!/usr/bin/env python3
"""
export_dsh_index.py — 将几何论文章库导出为 DeepSeek Harness 插件可读的离线索引。

数据源:   app/chroma_db（ChromaDB 持久化，文章分块与主库真理层）
          app/articles（markdown 原文）
产物:     dsh-geometry-plugin/data/
            articles.jsonl   — 文章分块（chunk_id, fname, article_id, start, end, text）
            truth.jsonl      — 主库真理层（permanent_number, formula_name, content, meta）
            articles/        — 全文 markdown（仅被索引的篇目，fname 对齐）
            articles_toc.json— 每篇章节表（level, title, offset）
            dict.json        — 中文术语词典（高频专名，供 BM25 分词）
            manifest.json    — 导出元信息

用法: python3 dsh-geometry-plugin/scripts/export_dsh_index.py
依赖: chromadb（与主应用共用 app/.venv）
"""
import os, sys, json, re
from collections import Counter
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DB = os.path.join(PROJECT_ROOT, 'app', 'chroma_db')
SRC_ARTICLES = os.path.join(PROJECT_ROOT, 'app', 'articles')
OUT_DIR = os.path.join(PROJECT_ROOT, 'dsh-geometry-plugin', 'data')
OUT_ARTICLES = os.path.join(OUT_DIR, 'articles')

# ---------- 词典抽取 ----------

# 常见中文虚词/高频组合，过滤候选词
CN_STOP = set('的了是在与和就不都一个也于这那呢吗吧啊很中为对此其或及并而但如若将把被从向对以可会要能最非常无有各该这些那些之我们你们他们自己已经正在还是就是因为所以但是然而如果那么虽然并且而且或者以及关于对于通过由于根据按照随着作为成为可以可能应该必须需要没有不是而是这个那个什么怎么怎样为什么如何哪里何时多少几些许多大量少部分等又再还则更却只')

def iter_cn_windows(text: str, min_len: int = 2, max_len: int = 6):
    """对每段连续中文串做滑窗，产出 2-6 字子串。"""
    for seg in re.findall(r'[\u4e00-\u9fff]{2,}', text):
        n = len(seg)
        if n < min_len:
            continue
        for L in range(min_len, min(max_len, n) + 1):
            for i in range(n - L + 1):
                yield seg[i:i + L]

def extract_terms(texts, min_freq=40, max_terms=600):
    cnt = Counter()
    for t in texts:
        for w in iter_cn_windows(t):
            cnt[w] += 1
    terms = []
    for w, c in cnt.most_common():
        if c < min_freq:
            break
        if w in CN_STOP:
            continue
        # 首尾虚词过滤：'的'/'了'/'在'/'是' 等作首尾的字常见于普通词组
        if w[0] in '的了在是把被从向着为以与和或及并且' or w[-1] in '的了在是把被从向着为以与和或及并且吗呢啊吧':
            continue
        terms.append(w)
        if len(terms) >= max_terms:
            break
    return terms

# ---------- 章节表 ----------

def build_toc(md_text: str):
    """扫描 markdown 标题，返回 [{level, title, offset}]。"""
    toc = []
    pos = 0
    for line in md_text.split('\n'):
        m = re.match(r'^(#{1,4})\s+(.+?)\s*$', line)
        if m:
            toc.append({'level': len(m.group(1)), 'title': m.group(2).strip(), 'offset': pos})
        pos += len(line) + 1  # +1 换行符
    return toc

# ---------- 主流程 ----------

def export_collection(client, name: str, out_base: str):
    col = client.get_collection(name)
    n = col.count()
    print(f"[export] {name}: {n} 条")
    if n == 0:
        # 集合为空时不覆盖旧 jsonl（保留历史导出数据），但返回实际行数供 manifest 使用
        out_path = os.path.join(OUT_DIR, f'{out_base}.jsonl')
        if os.path.exists(out_path):
            with open(out_path, encoding='utf-8') as f:
                old_n = sum(1 for line in f if line.strip())
            print(f"[export] {name} 集合为空，保留旧文件 {old_n} 条")
            return old_n
        return 0
    got = col.get(include=['metadatas', 'documents'])
    rows, metas, docs = got['ids'], got['metadatas'], got['documents']
    lines = []
    for cid, meta, doc in zip(rows, metas, docs):
        rec = {'chunk_id': cid}
        if isinstance(meta, dict):
            for k in ('fname', 'article_id', 'start', 'end', 'source', 'permanent_number',
                      'formula_name', 'verified_at', 'topology_class', 'status',
                      'series', 'title', 'version'):
                if k in meta:
                    rec[k] = meta[k]
        rec['text'] = doc or ''
        lines.append(json.dumps(rec, ensure_ascii=False))
    with open(os.path.join(OUT_DIR, f'{out_base}.jsonl'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return n

def main():
    import chromadb
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(OUT_ARTICLES, exist_ok=True)
    client = chromadb.PersistentClient(path=SRC_DB)

    # 1. 分块导出（不再导出向量 .bin —— 纯 BM25 方案）
    n_articles = export_collection(client, 'articles', 'articles')
    n_truth = export_collection(client, 'master_truth', 'truth')

    # 2. 全文打包：以分块 fname 对齐，只打包被索引的篇目
    chunks = []
    with open(os.path.join(OUT_DIR, 'articles.jsonl'), encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    fnames = sorted({c.get('fname', '') for c in chunks if c.get('fname')})
    print(f"[export] 被索引文件数: {len(fnames)}")
    missing, copied = [], 0
    toc_all = {}
    texts_for_dict = []
    for fn in fnames:
        src = os.path.join(SRC_ARTICLES, fn)
        dst = os.path.join(OUT_ARTICLES, fn)
        if not os.path.exists(src):
            missing.append(fn)
            continue
        md = open(src, encoding='utf-8').read()
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'w', encoding='utf-8').write(md)
        toc_all[fn] = build_toc(md)
        texts_for_dict.append(md)
        copied += 1
    if missing:
        print(f"[export] WARN 未找到原文文件（仍保留分块）: {missing[:10]} ... 共 {len(missing)}")
    with open(os.path.join(OUT_DIR, 'articles_toc.json'), 'w', encoding='utf-8') as f:
        json.dump(toc_all, f, ensure_ascii=False)
    print(f"[export] 全文打包: {copied} 篇 → {OUT_ARTICLES}")

    # 3. 术语词典（从全文统计）
    terms = extract_terms(texts_for_dict)
    print(f"[export] 术语词典: {len(terms)} 词")
    with open(os.path.join(OUT_DIR, 'dict.json'), 'w', encoding='utf-8') as f:
        json.dump({'model': 'bm25-mixed-tokenizer', 'terms': terms}, f, ensure_ascii=False, indent=1)

    # 4. manifest
    manifest = {
        'exported_at': datetime.now().isoformat(timespec='seconds'),
        'retrieval': 'BM25 (offline, no embeddings)',
        'source_db': 'app/chroma_db',
        'source_articles': 'app/articles',
        'counts': {'chunks': n_articles, 'truth': n_truth, 'files': copied},
        'dict_terms': len(terms),
    }
    with open(os.path.join(OUT_DIR, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[export] 完成 → {OUT_DIR}")
    total = 0
    for root, _, files in os.walk(OUT_DIR):
        for fn in files:
            p = os.path.join(root, fn)
            sz = os.path.getsize(p)
            total += sz
            rel = os.path.relpath(p, OUT_DIR)
            print(f"  {rel}: {sz/1024:.0f} KB")
    print(f"[export] 总计: {total/1024/1024:.1f} MB")

if __name__ == '__main__':
    main()
