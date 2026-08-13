#!/bin/bash
AUDIO="/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py"
echo "=== _transcribe_openai 完整头部（615-665 行） ==="
echo 'ab640815.' | sudo -S sed -n '615,665p' $AUDIO
echo ""
echo "=== 调用点：filename 从哪来（890-920 行） ==="
echo 'ab640815.' | sudo -S sed -n '885,920p' $AUDIO
