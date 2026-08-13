#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo "=== 1. 函数定位 ==="
grep -n "async def _transcribe_openai\|async def transcription_handler\|async def transcribe\|async def transcription" $AUDIO_PY
echo ""
echo "=== 2. _transcribe_openai 完整代码 ==="
START=$(grep -n "async def _transcribe_openai" $AUDIO_PY | head -1 | cut -d: -f1)
END=$((START + 75))
sed -n "${START},${END}p" $AUDIO_PY
