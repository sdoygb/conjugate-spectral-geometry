#!/bin/bash
echo "=== 1. 对话测试（共扼谱几何问题，验证向量检索链路） ==="
curl -s -X POST http://localhost:5000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"请用共扼谱几何介绍什么是谱刚性，并说明 S_e 锁定的含义。"}],"stream":false}' \
  --max-time 180 | python3 -c "import sys,json; d=json.load(sys.stdin); print('model:',d.get('model')); print('finish:',d.get('choices',[{}])[0].get('finish_reason')); print('reply:',d.get('choices',[{}])[0].get('message',{}).get('content','')[:800])" 2>&1
echo ""
echo "=== 2. 模型列表（验证多模型配置生效） ==="
curl -s http://localhost:5000/v1/models --max-time 15 | head -c 1500
echo ""
echo "=== 3. 检索命中日志 ==="
journalctl -u geometry-ai --no-pager --since "3 minutes ago" | grep -E "检索|VECTOR|RAG|hit" | tail -5
