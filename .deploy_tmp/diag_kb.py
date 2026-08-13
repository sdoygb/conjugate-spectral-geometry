import sys, os
sys.path.insert(0, '/usr/local/geometry-ai')
os.chdir('/usr/local/geometry-ai')
from dotenv import load_dotenv
load_dotenv('/usr/local/geometry-ai/.env')
from knowledge import VectorKnowledgeBase

kb = VectorKnowledgeBase('/usr/local/geometry-ai/chroma_db')
ok = kb.initialize()
print("initialize:", ok)
print("_initialized:", kb._initialized)
print("articles_collection:", kb.articles_collection)
print("articles_count:", kb.articles_count)
print("total_docs:", kb.total_docs)
print("bm25 initialized:", kb.bm25_searcher.initialized)
print("bm25 jieba:", kb.bm25_searcher._jieba_loaded)

r = kb.search('谱刚性', top_k=8)
print("search('谱刚性') 结果数:", len(r))
for x in r[:3]:
    print("  -", str(x.get('label',''))[:70], "| dist:", x.get('distance'))
r2 = kb.search('S_e 锁定 谱刚性 几何', top_k=8)
print("search('S_e 锁定 谱刚性 几何') 结果数:", len(r2))
for x in r2[:3]:
    print("  -", str(x.get('label',''))[:70], "| dist:", x.get('distance'))
