#!/bin/bash
echo "=== _transcribe_openai 当前完整代码（650-720行） ==="
sed -n '650,720p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo ""
echo "=== 180-215 行（transcode/convert 相关） ==="
sed -n '180,215p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo ""
echo "=== 370-400 行（transcription 端点保存逻辑） ==="
sed -n '370,400p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
