#!/bin/bash
nohup curl -s -X POST http://localhost:5000/v1/vector/rebuild > /tmp/rebuild_result.txt 2>&1 &
echo "REBUILD_STARTED pid=$!"
sleep 3
ls -la /tmp/rebuild_result.txt
echo "---LOG---"
journalctl -u geometry-ai --no-pager -n 3 | tail -3
