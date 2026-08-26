#!/usr/bin/env python3
"""
backfill_chroma.py — 将缺失的文章分块补录进 app/chroma_db 的 articles 集合。

分块逻辑与 app/knowledge.py 的 smart_chunk 完全一致（CHUNK_SIZE=1000, CHUNK_OVERLAP=200），
嵌入使用 fastembed 的 BAAI/bge-small-zh-v1.5（512 维，与现有集合一致，已验证余弦相似度 1.0）。
chunk_id 格式同 knowledge.py: art_{article_id}_{md5(fname)[:6]}_{start}_{end}
"""
import os, sys, re, hashlib, json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'app', 'chroma_db')
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'app', 'articles')
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# 待补录：app/articles 中有、chroma 中没有的 3 篇
TARGETS = [
    '10.70_几何POVM与Zeno冻结_CN_260822.md',
    '3.13_几何量子势与非线性演化_Madelung分解_CN_260825.md',
    '3.14_呼吸模式的含时方程_CN_260825.md',
]

def smart_chunk(content: str, article_id: str, fname: str):
    """与 app/knowledge.py smart_chunk 完全一致的分块逻辑"""
    chunks = []
    start = 0
    length = len(content)
    while start < length:
        target_end = min(start + CHUNK_SIZE, length)
        if target_end < length:
            search_range = content[target_end:min(target_end + 200, length)]
            best_break = target_end
            para_match = re.search(r'\n\n', search_range)
            if para_match:
                best_break = target_end + para_match.start()
            else:
                sentence_end = re.search(r'[\u3002\.\?\!]\s', search_range)
                if sentence_end:
                    best_break = target_end + sentence_end.start() + 2
            target_end = min(best_break, length)
        chunk_text = content[start:target_end]
        chunks.append({
            'article_id': article_id,
            'fname': fname,
            'text': chunk_text,
            'start': start,
            'end': target_end
        })
        start += max(target_end - start - CHUNK_OVERLAP, CHUNK_SIZE // 2)
    return chunks

def main():
    import chromadb
    from fastembed import TextEmbedding

    client = chromadb.PersistentClient(path=DB_PATH)
    col = client.get_collection('articles')

    # 已存在的 fname（防止重复）
    got = col.get(include=['metadatas'], limit=100000)
    existing = {m['fname'] for m in got['metadatas'] if m and m.get('fname')}
    print(f"[backfill] chroma 现有文件数: {len(existing)}")

    model = TextEmbedding('BAAI/bge-small-zh-v1.5')

    total_added = 0
    for fname in TARGETS:
        fpath = os.path.join(ARTICLES_DIR, fname)
        if not os.path.exists(fpath):
            print(f"[backfill] SKIP 文件不存在: {fname}")
            continue
        if fname in existing:
            print(f"[backfill] SKIP 已在 chroma: {fname}")
            continue

        content = open(fpath, encoding='utf-8').read()
        article_id = fname
        chunks = smart_chunk(content, article_id, fname)
        if not chunks:
            print(f"[backfill] SKIP 无分块: {fname}")
            continue

        fname_hash = hashlib.md5(fname.encode()).hexdigest()[:6]
        ids, documents, metadatas = [], [], []
        for chunk in chunks:
            cid = f"art_{article_id}_{fname_hash}_{chunk['start']}_{chunk['end']}"
            ids.append(cid)
            documents.append(chunk['text'])
            metadatas.append({
                "article_id": chunk['article_id'],
                "fname": chunk['fname'],
                "start": chunk['start'],
                "end": chunk['end'],
                "source": "articles",
                "chunk_id": cid,
            })

        # 生成向量
        embeddings = [e.tolist() for e in model.embed(documents)]
        dims = {len(e) for e in embeddings}
        assert dims == {512}, f"嵌入维度异常: {dims}"

        col.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        total_added += len(chunks)
        print(f"[backfill] 已补录 {fname}: {len(chunks)} 块 (维度 {dims.pop()})")

    n = col.count()
    print(f"[backfill] 完成: 共新增 {total_added} 块, articles 集合总计 {n} 条")

    # 校验：3 篇应都在
    got2 = col.get(include=['metadatas'], limit=100000)
    fnames2 = {m['fname'] for m in got2['metadatas'] if m and m.get('fname')}
    missing = [f for f in TARGETS if f not in fnames2]
    print(f"[backfill] 校验: 目标 3 篇全部在 chroma = {not missing}")
    if missing:
        print(f"[backfill] 仍缺失: {missing}")
        sys.exit(1)

if __name__ == '__main__':
    main()
