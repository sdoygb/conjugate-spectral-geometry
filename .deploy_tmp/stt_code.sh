#!/bin/bash
AUDIO="/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py"
echo "=== 1. _transcribe_openai 实现（660-740 行） ==="
echo 'ab640815.' | sudo -S sed -n '660,740p' $AUDIO
echo ""
echo "=== 2. api_request_format 相关代码 ==="
echo 'ab640815.' | sudo -S grep -n "api_request_format\|request_format\|multipart\|FormData\|form_data" $AUDIO | head -20
