#!/bin/bash
echo "=== 最终 health ==="
curl -s --max-time 5 http://127.0.0.1:5000/health | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('articles_count:', d.get('articles_count'))
print('total_docs:', d.get('total_docs'))
print('vector_kb_initialized:', d.get('vector_kb_initialized'))
print('build_date:', d.get('build_date'))
"
echo ""
echo "=== 检索端点查找 ==="
grep -n "@app.route('/v1/vector\|@app.route('/v1/search\|def .*search" /usr/local/geometry-ai/server.py | head -10
echo ""
echo "=== 向量库磁盘状态 ==="
du -sh /usr/local/geometry-ai/chroma_db 2>/dev/null
ls -la /usr/local/geometry-ai/chroma_db/chroma.sqlite3 2>/dev/null
