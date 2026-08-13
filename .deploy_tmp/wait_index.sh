#!/bin/bash
# 等待索引构建完成，最多等 10 分钟
for i in $(seq 1 60); do
    sleep 10
    DONE=$(journalctl -u geometry-ai --no-pager --since "5 minutes ago" | grep -c "向量索引构建成功\|已有向量索引")
    ERR=$(journalctl -u geometry-ai --no-pager --since "5 minutes ago" | grep -c "向量索引构建失败\|Traceback")
    if [ "$DONE" -gt 0 ]; then
        echo "INDEX_DONE after ~$((i*10))s"
        journalctl -u geometry-ai --no-pager -n 30 | grep -E "STARTUP|VECTOR|ERROR" | tail -12
        exit 0
    fi
    if [ "$ERR" -gt 0 ]; then
        echo "INDEX_FAILED after ~$((i*10))s"
        journalctl -u geometry-ai --no-pager -n 50 | grep -E "STARTUP|VECTOR|ERROR|Traceback" | tail -20
        exit 1
    fi
done
echo "TIMEOUT 10min, current log:"
journalctl -u geometry-ai --no-pager -n 20 | grep -E "VECTOR|STARTUP" | tail -10
