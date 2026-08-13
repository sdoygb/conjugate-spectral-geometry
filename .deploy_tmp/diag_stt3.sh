#!/bin/bash
echo "=== 1. 缓存音频文件 ==="
ls -la /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/ 2>/dev/null | tail -12
echo ""
echo "=== 2. _transcribe_openai 代码（640-720行） ==="
sed -n '640,720p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo ""
echo "=== 3. convert_audio_to_mp3 代码（120-200行） ==="
sed -n '120,200p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
