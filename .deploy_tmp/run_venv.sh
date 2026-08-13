#!/bin/bash
nohup bash -c "echo 'ab640815.' | sudo -S bash /tmp/create_venv.sh > /tmp/venv_setup.log 2>&1" &
echo "STARTED pid=$!"
sleep 3
head -10 /tmp/venv_setup.log 2>/dev/null
