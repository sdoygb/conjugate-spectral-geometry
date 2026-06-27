import sys, os
sys.path.insert(0, 'app')
os.chdir('app')
from knowledge import VectorKnowledgeBase
kb = VectorKnowledgeBase('chroma_db')
kb.initialize()

# 1. 删除目录总纲（模糊匹配）
try:
    all_data = kb.articles_collection.get(include=['metadatas'])
    if all_data and all_data['metadatas']:
        to_delete = []
        for i, meta in enumerate(all_data['metadatas']):
            fname = meta.get('fname', '')
            if fname.startswith('目录_') or 'archive' in fname:
                to_delete.append(all_data['ids'][i])
        if to_delete:
            kb.articles_collection.delete(ids=to_delete)
            print(f'删除了 {len(to_delete)} 个目录/archive 索引块')
        else:
            print('没有找到目录/archive 文件索引（可能已删除）')
    print(f'articles 集合剩余: {kb.articles_collection.count()} 块')
except Exception as e:
    print(f'操作失败: {e}')

# 2. 清空 learned 集合
cleared = kb.clear_learned()
print(f'learned 集合清空: {cleared}')