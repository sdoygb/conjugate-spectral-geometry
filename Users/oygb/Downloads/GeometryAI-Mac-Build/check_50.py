import os, sys, re
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/app')
os.chdir('/Users/oygb/Downloads/GeometryAI-Mac-Build/app')

from chromadb.config import Settings
import chromadb

# 1. 检查同目录下文件
articles_dir = 'articles'
fnames = sorted(os.listdir(articles_dir))
print(f"文件总数: {len(fnames)}")

for fn in fnames:
    if '50' in fn or '数的几何' in fn:
        print(f"FOUND: {fn}")
        fpath = os.path.join(articles_dir, fn)
        size = os.path.getsize(fpath)
        print(f"  大小: {size} 字节")

# 2. 测试正则匹配
test_names = ['50_数的几何_修订版.md', '1_Hydrogen_Atom.md', '49_七级.md']
for tn in test_names[:1]:
    match = re.match(r'([\d.]+|AI-\d+)', tn)
    print(f"  '{tn}' -> article_id='{match.group(1) if match else 'NONE'}'")

# 3. ChromaDB检查所有文章的fname
client = chromadb.PersistentClient(path='chroma_db', settings=Settings(anonymized_telemetry=False))
col = client.get_collection('articles')
results = col.get(limit=5000)
metadatas = results.get('metadatas', [])

all_fnames = set()
for meta in metadatas:
    if meta:
        all_fnames.add(meta.get('fname', '?'))
print(f"\nChromaDB中共有 {len(all_fnames)} 个不同的fname:")
for fn in sorted(all_fnames):
    print(f"  {fn}")