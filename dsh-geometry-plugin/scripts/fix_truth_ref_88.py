#!/usr/bin/env python3
"""
fix_truth_ref_88.py — 修正真理库中 #88 的编号引用错误。

问题：5 条记录（#2、#3、#439、#440、#526）把「引理 0.2.2.01（半单分裂）」错标为 #88，
正确编号是 #183（#88 实为「引理 1.2.2.01 Schur 刚性」）。

替换规则（仅当 #88 与 0.2.2.01 上下文关联时）：
  - "0.2.2.01（#88"  → "0.2.2.01（#183"
  - "#88（引理 0.2.2.01" → "#183（引理 0.2.2.01"

修正对象：主库 master_ai/master_chroma_db 的 master_formulas collection（权威源）。
修正后由 sync_master_truth.py 重新同步中间层，export_dsh_index.py 重新导出。
"""
import os, sys, re, json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER_DB = os.path.join(PROJECT_ROOT, 'master_ai', 'master_chroma_db')

TARGETS = {'2', '3', '439', '440', '526'}

# 两种错误引用模式（均与 0.2.2.01 上下文绑定）
PATTERN_A = re.compile(r'0\.2\.2\.01（#88')     # 正文推导链: 由引理 0.2.2.01（#88）
PATTERN_B = re.compile(r'#88（引理 0\.2\.2\.01')  # 依赖标注: #88（引理 0.2.2.01 半单分裂）

def fix_doc(doc: str) -> tuple:
    """返回 (修正后文本, 替换次数)"""
    n = 0
    new = PATTERN_A.sub(lambda m: '0.2.2.01（#183', doc)
    if new != doc:
        n += len(PATTERN_A.findall(doc))
    doc = new
    new = PATTERN_B.sub(lambda m: '#183（引理 0.2.2.01', doc)
    if new != doc:
        n += len(PATTERN_B.findall(doc))
    return new, n

def main():
    import chromadb
    # 主库 embedding: SiliconFlow bge-m3 (1024 维)，与 master_ai/master_db.py 一致
    import openai, httpx, os as _os
    api_key = _os.getenv('SILICONFLOW_API_KEY', '')
    if not api_key:
        # 尝试读取 master_ai/.env
        env_path = os.path.join(PROJECT_ROOT, 'master_ai', '.env')
        if os.path.exists(env_path):
            for line in open(env_path):
                if line.startswith('SILICONFLOW_API_KEY='):
                    api_key = line.strip().split('=', 1)[1]
    assert api_key, "未找到 SILICONFLOW_API_KEY"
    sf = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1",
        http_client=httpx.Client(trust_env=False),
        timeout=30.0,
        max_retries=2,
    )
    def embed(texts):
        out = []
        for t in texts:
            t = t.replace('\x00', '').replace('\r', '')
            import re as _re
            t = _re.sub(r'\s+', ' ', t).strip()[:2000]
            if not t:
                out.append([0.0] * 1024)
                continue
            resp = sf.embeddings.create(model='BAAI/bge-m3', input=[t])
            out.extend([d.embedding for d in resp.data])
        return out

    client = chromadb.PersistentClient(path=MASTER_DB)
    col = client.get_collection('master_formulas')
    got = col.get(include=['documents', 'metadatas'], limit=100000)

    updates = []
    for i, mid in enumerate(got['ids']):
        meta = got['metadatas'][i]
        pn = str(meta.get('permanent_number'))
        if pn not in TARGETS:
            continue
        doc = got['documents'][i]
        fixed, n = fix_doc(doc)
        if n == 0:
            print(f"[fix] #{pn} ({meta.get('formula_name')}) 未匹配到可替换模式，跳过")
            continue
        # 校验：替换后不应再有上下文错误的 #88
        assert '0.2.2.01（#88' not in fixed, f"#{pn} 仍含错误模式A"
        assert '#88（引理 0.2.2.01' not in fixed, f"#{pn} 仍含错误模式B"
        # 且确认 #183 已就位
        assert '#183' in fixed, f"#{pn} 未写入 #183"
        updates.append((mid, fixed))
        print(f"[fix] #{pn} ({meta.get('formula_name')}) 修正 {n} 处: {mid}")

    if not updates:
        print("[fix] 无待修正记录")
        return

    # 批量写入（chunk_id 不变，仅更新 document + 重新嵌入 1024 维）
    ids = [u[0] for u in updates]
    docs = [u[1] for u in updates]
    print(f"[fix] 为 {len(docs)} 条生成 1024 维嵌入...")
    embs = embed(docs)
    assert all(len(e) == 1024 for e in embs), "嵌入维度错误"
    col.update(ids=ids, documents=docs, embeddings=embs)
    print(f"[fix] 主库 master_formulas 已更新 {len(updates)} 条")

    # 复检
    got2 = col.get(include=['documents', 'metadatas'], limit=100000)
    ok = True
    for i, mid in enumerate(got2['ids']):
        meta = got2['metadatas'][i]
        if str(meta.get('permanent_number')) in TARGETS:
            doc = got2['documents'][i]
            if '0.2.2.01（#88' in doc or '#88（引理 0.2.2.01' in doc:
                print(f"[fix] 复检失败: #{meta.get('permanent_number')}")
                ok = False
    print(f"[fix] 复检: {'全部通过' if ok else '存在失败'}")
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
