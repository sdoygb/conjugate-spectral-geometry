#!/bin/bash
echo "=== 1. 实测 chromadb 1.5.9 是否接受 embedding_function 参数 ==="
echo 'ab640815.' | sudo -S /usr/local/geometry-ai/venv/bin/python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/tmp/test_chroma159')
try:
    col = client.get_or_create_collection('t', embedding_function=lambda x: x)
    print('RESULT: embedding_function 参数被接受')
except TypeError as e:
    print('RESULT: TypeError ->', str(e)[:120])
except Exception as e:
    print('RESULT:', type(e).__name__, str(e)[:120])
" 2>&1 | grep -E "RESULT|Error" | head -3
echo ""
echo "=== 2. open_webui 包内 chromadb API 用法 ==="
grep -rn "get_or_create_collection\|create_collection\|embedding_function" /usr/local/geometry-ai/venv/lib/python3.12/site-packages/open_webui/ 2>/dev/null | grep -v "\.pyc" | head -12
echo ""
echo "=== 3. open_webui 依赖 chromadb 的模块 ==="
grep -rln "import chromadb\|from chromadb" /usr/local/geometry-ai/venv/lib/python3.12/site-packages/open_webui/ 2>/dev/null | grep -v "\.pyc" | head -8
echo ""
echo "=== 4. chromadb 0.6.3 兼容性确认（当前 geometry-ai 要求） ==="
grep -rn "chromadb" /usr/local/geometry-ai/requirements.txt 2>/dev/null || echo "requirements.txt 无 chromadb 行"
