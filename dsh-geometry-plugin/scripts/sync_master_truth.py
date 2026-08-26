#!/usr/bin/env python3
"""
sync_master_truth.py — 从主库（master-ai）拉取真理层，全量写入 app/chroma_db 的 master_truth 集合。

嵌入使用 fastembed 的 BAAI/bge-small-zh-v1.5（512 维，与现有集合 embedding_dim=512 一致）。
id 使用主库 master_id；元数据字段与 app/master_client.py 的 _store_truth_locally 对齐。
"""
import os, sys, json, requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, 'app', 'chroma_db')
MASTER_URL = os.getenv('MASTER_AI_URL', 'http://localhost:5001')
MASTER_TOKEN = os.getenv('MASTER_AI_TOKEN', 'master-ai-verify')

def main():
    import chromadb
    from fastembed import TextEmbedding

    # 1. 拉取主库真理
    resp = requests.get(f"{MASTER_URL}/v1/master/truth",
                        headers={'Authorization': f'Bearer {MASTER_TOKEN}'},
                        timeout=30, proxies={"http": None, "https": None})
    resp.raise_for_status()
    data = resp.json()
    formulas = data.get('formulas', [])
    print(f"[sync] 主库真理层: {data.get('count')} 条 (master_total={data.get('master_total')})")

    if not formulas:
        print("[sync] 主库无公式，中止")
        sys.exit(1)

    # 2. 嵌入模型
    model = TextEmbedding('BAAI/bge-small-zh-v1.5')

    # 3. 构建记录
    ids, documents, metadatas = [], [], []
    for f in formulas:
        mid = f.get('master_id') or f"truth_{f.get('permanent_number', 0)}"
        ids.append(mid)
        documents.append(f.get('document', ''))
        metadatas.append({
            "master_id": mid,
            "permanent_number": str(f.get('permanent_number', 0)),
            "formula_name": f.get('formula_name', ''),
            "verified_at": f.get('verified_at', ''),
            "source": "master_ai",
            "readonly": "true",
        })

    # 去重保护
    assert len(set(ids)) == len(ids), f"master_id 重复: {len(ids)} vs {len(set(ids))}"
    assert len(set(m['permanent_number'] for m in metadatas)) == len(metadatas), "permanent_number 重复"

    print(f"[sync] 待写入: {len(ids)} 条，生成嵌入中...")
    embeddings = [e.tolist() for e in model.embed(documents)]
    dims = {len(e) for e in embeddings}
    assert dims == {512}, f"嵌入维度异常: {dims}"

    # 4. 全量替换写入
    client = chromadb.PersistentClient(path=DB_PATH)
    col = client.get_or_create_collection(
        name="master_truth",
        metadata={"description": "主库下发的已验证真理（只读，不可修改）"},
    )
    existing = col.get()
    if existing['ids']:
        col.delete(ids=existing['ids'])
        print(f"[sync] 已清空旧数据 {len(existing['ids'])} 条")

    # 分小批写入（避免单批过大）
    BATCH = 200
    for i in range(0, len(ids), BATCH):
        col.add(
            ids=ids[i:i+BATCH],
            documents=documents[i:i+BATCH],
            metadatas=metadatas[i:i+BATCH],
            embeddings=embeddings[i:i+BATCH],
        )
    n = col.count()
    print(f"[sync] 完成: master_truth 集合 {n} 条")

    if n != len(ids):
        print(f"[sync] 警告: 写入数 {n} != 期望 {len(ids)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
