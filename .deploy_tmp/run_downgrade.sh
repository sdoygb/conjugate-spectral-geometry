#!/bin/bash
nohup bash -c "echo 'ab640815.' | sudo -S bash /tmp/downgrade_chroma.sh > /tmp/downgrade.log 2>&1" &
echo "STARTED pid=$!"
sleep 3
head -5 /tmp/downgrade.log 2>/dev/null
