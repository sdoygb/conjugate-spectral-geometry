#!/bin/bash
F=$(ls -t /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/*.wav 2>/dev/null | head -1)
echo "使用文件: $F"
SECRET=$(systemctl cat open-webui 2>/dev/null | grep WEBUI_SECRET_KEY | head -1 | cut -d= -f2- | tr -d '"')
WEBUI_SECRET_KEY="$SECRET" OPENWEBUI_DATA_DIR=/usr/local/geometry-ai/webui_data \
  /usr/local/open-webui-venv/bin/python3 /tmp/run_transcribe.py "$F" 2>&1 | tail -25
