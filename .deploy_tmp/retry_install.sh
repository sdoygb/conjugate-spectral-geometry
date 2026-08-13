#!/bin/bash
nohup /usr/local/open-webui-venv/bin/pip install open-webui==0.11.0 --resume-retries 10 > /tmp/owui_install2.log 2>&1 &
echo "RETRY_PID=$!"
sleep 5
tail -2 /tmp/owui_install2.log
