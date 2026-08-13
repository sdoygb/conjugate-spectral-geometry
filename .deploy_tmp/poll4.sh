#!/bin/bash
sleep 100
echo "=== 最后8行原始日志 ==="
journalctl -u geometry-ai --no-pager -n 8 2>&1 | tail -8
echo "=== 关键标记 ==="
journalctl -u geometry-ai --no-pager 2>&1 | grep -E "向量索引构建成功|向量索引构建失败|已有向量索引|教学系统" | tail -5
