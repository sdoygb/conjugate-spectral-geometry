#!/bin/bash
# 等待索引完成（最长900秒），结果写 /tmp/index_wait.txt
for i in $(seq 1 90); do
  sleep 10
  if journalctl -u geometry-ai --no-pager --since "20 minutes ago" | grep -q "向量索引构建成功"; then
    echo "INDEX_DONE $(date +%H:%M:%S) after ~$((i*10))s" > /tmp/index_wait.txt
    journalctl -u geometry-ai --no-pager -n 30 | grep -E "STARTUP|VECTOR" | tail -8 >> /tmp/index_wait.txt
    exit 0
  fi
done
echo "TIMEOUT_900s $(date +%H:%M:%S)" > /tmp/index_wait.txt
journalctl -u geometry-ai --no-pager -n 3 >> /tmp/index_wait.txt
