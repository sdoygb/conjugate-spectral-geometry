#!/bin/bash
nohup bash -c "echo 'ab640815.' | sudo -S env TMPDIR=/var/tmp /usr/local/open-webui-venv/bin/pip install open-webui==0.11.0 --resume-retries 10 -i https://pypi.tuna.tsinghua.edu.cn/simple > /tmp/owui_install4.log 2>&1" &
echo "RETRY4_STARTED pid=$!"
