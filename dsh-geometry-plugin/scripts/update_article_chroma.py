#!/usr/bin/env python3
"""update_article_chroma.py — 用本地 512 维嵌入更新 chroma 中单篇文章的分块
（删除旧分块 → 重新分块嵌入 → 加入）。"""
import os, sys, re, hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'app', 'chroma_db')
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'app', 'articles')
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def smart_chunk(content, article_id, fname):
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
        chunks.append({'article_id': article_id, 'fname': fname,
                       'text': content[start:target_end],
                       'start': start, 'end': target_end})
        start += max(target_end - start - CHUNK_OVERLAP, CHUNK_SIZE // 2)
    return chunks


def get_local_ef():
    """返回与主应用 knowledge.LocalEmbeddingFunction 同名的 EF，
    使 get_or_create 与集合持久化配置一致（避免 EF 冲突）。"""
    import sys
    app_dir = os.path.join(PROJECT_ROOT, 'app')
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    from knowledge import LocalEmbeddingFunction
    return LocalEmbeddingFunction()


def main():
    fname = sys.argv[1]
    fpath = os.path.join(ARTICLES_DIR, fname)
    if not os.path.exists(fpath):
        print(f"文件不存在: {fpath}")
        return
    import chromadb
    from fastembed import TextEmbedding
    client = chromadb.PersistentClient(path=DB_PATH)
    col = client.get_or_create_collection(
        'articles', embedding_function=get_local_ef())

    # 删除该文章旧分块
    got = col.get(include=['metadatas'], limit=100000)
    old_ids = [i for i, m in zip(got['ids'], got['metadatas'])
               if m and m.get('fname') == fname]
    if old_ids:
        col.delete(ids=old_ids)
        print(f"[update] 已删除旧分块 {len(old_ids)} 条: {fname}")

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
    model = TextEmbedding('BAAI/bge-small-zh-v1.5')
    embs = [e.tolist() for e in model.embed(documents)]
    col.add(ids=ids, documents=documents, metadatas=metadatas,
            embeddings=embs)
    print(f"[update] 已重新入库 {len(chunks)} 块 (512维), "
          f"集合总计 {col.count()}")


if __name__ == '__main__':
    main()
