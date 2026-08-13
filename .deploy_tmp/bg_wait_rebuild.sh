#!/bin/bash
# 等待 rebuild 完成（最长 1200 秒），结果写 /tmp/rebuild_wait.txt
for i in $(seq 1 120); do
  sleep 10
  if [ -s /tmp/rebuild_result.txt ]; then
    echo "REBUILD_DONE at $(date +%H:%M:%S) after ~$((i*10))s"
    echo "---RESULT---"
    cat /tmp/rebuild_result.txt
    echo "---BM25LOG---"
    journalctl -u geometry-ai --no-pager --since "20 minutes ago" | grep -E "BM25|索引完成|重建" | tail -5
    exit 0
  fi
done
echo "TIMEOUT_1200s at $(date +%H:%M:%S)"
journalctl -u geometry-ai --no-pager -n 5 | tail -5
