#!/bin/bash
echo "=== 1. open-webui 0.11.0 RAG embedding 配置变量 ==="
grep -n "RAG_EMBEDDING" /usr/local/geometry-ai/venv/lib/python3.12/site-packages/open_webui/config.py | head -20
echo ""
echo "=== 2. retrieval get_ef 逻辑（embedding 引擎选择） ==="
grep -n "def get_ef\|RAG_EMBEDDING_ENGINE\|sentence_transformers\|SentenceTransformer" /usr/local/geometry-ai/venv/lib/python3.12/site-packages/open_webui/routers/retrieval.py | head -15
echo ""
echo "=== 3. pip 依赖冲突详情 ==="
grep -A5 "dependency conflicts" /tmp/downgrade.log | head -15
echo ""
echo "=== 4. open-webui 当前生效的 RAG 环境变量 ==="
cat /proc/$(pgrep -f "open-webui serve" | head -1)/environ 2>/dev/null | tr '\0' '\n' | grep -E "RAG_|OFFLINE|ENABLE_UPDATE" || echo "无法读取"
