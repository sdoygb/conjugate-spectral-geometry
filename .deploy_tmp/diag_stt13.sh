#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo "=== transcribe() 尾部完整代码（1082-1125行） ==="
sed -n '1082,1125p' $AUDIO_PY
