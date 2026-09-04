#!/usr/bin/env python3
"""rebuild_articles_512.py — 用本地 fastembed BAAI/bge-small-zh-v1.5（512 维）
全量重建 chroma 的 articles 集合（与主应用 GAI_EMBEDDING_MODE=local 一致）。
覆盖 app/articles 下全部 markdown（含新文章），chunk_id 格式与 knowledge.py
一致。"""
import os, sys, re, hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'app', 'chroma_db')
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'app', 'articles')
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def smart_chunk(content: str, article_id: str, fname: str):
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
        chunks.append({'article_id': article_id, 'fname': fname,
                       'text': chunk_text, 'start': start, 'end': target_end})
        start += max(target_end - start - CHUNK_OVERLAP, CHUNK_SIZE // 2)
    return chunks


def get_local_ef():
    """返回与主应用 knowledge.LocalEmbeddingFunction 同名的 EF，
    使集合持久化配置与中间层 initialize() 匹配（避免 'persisted: default' 冲突）。"""
    import sys
    app_dir = os.path.join(PROJECT_ROOT, 'app')
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from knowledge import LocalEmbeddingFunction
    return LocalEmbeddingFunction()


def main():
    import chromadb
    from fastembed import TextEmbedding

    client = chromadb.PersistentClient(path=DB_PATH)
    # 删除旧集合，重建 512 维（必须传入与主应用一致的 embedding_function，
    # 否则集合持久化为 'default' 配置，中间层 initialize() 会报 EF 冲突）
    try:
        client.delete_collection('articles')
        print("[rebuild] 已删除旧 articles 集合")
    except Exception as e:
        print(f"[rebuild] 删除失败(可能不存在): {e}")
    ef = get_local_ef()
    col = client.create_collection(
        name='articles',
        metadata={"description": "几何论文章知识（本地 bge-small-zh 512 维）"},
        embedding_function=ef)

    model = TextEmbedding('BAAI/bge-small-zh-v1.5')
    fnames = sorted(f for f in os.listdir(ARTICLES_DIR) if f.endswith('.md'))
    total = 0
    for fname in fnames:
        fpath = os.path.join(ARTICLES_DIR, fname)
        content = open(fpath, encoding='utf-8').read()
        chunks = smart_chunk(content, fname, fname)
        fname_hash = hashlib.md5(fname.encode()).hexdigest()[:6]
        ids, documents, metadatas = [], [], []
        for chunk in chunks:
            cid = f"art_{fname}_{fname_hash}_{chunk['start']}_{chunk['end']}"
            ids.append(cid)
            documents.append(chunk['text'])
            metadatas.append({'article_id': chunk['article_id'],
                              'fname': chunk['fname'],
                              'start': chunk['start'], 'end': chunk['end'],
                              'source': 'articles', 'chunk_id': cid})
        # 分批嵌入（每批 64）
        for i in range(0, len(documents), 64):
            batch_docs = documents[i:i + 64]
            batch_ids = ids[i:i + 64]
            batch_meta = metadatas[i:i + 64]
            embs = [e.tolist() for e in model.embed(batch_docs)]
            col.add(ids=batch_ids, documents=batch_docs,
                    metadatas=batch_meta, embeddings=embs)
        total += len(chunks)
        print(f"  [ok] {fname}: {len(chunks)} 块")
    print(f"[rebuild] 完成: {len(fnames)} 篇, {total} 块, "
          f"集合总计 {col.count()}")


if __name__ == '__main__':
    main()
