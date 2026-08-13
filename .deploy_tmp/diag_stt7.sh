#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo "=== 1. transcribe() 剩余代码（1085-1145行） ==="
sed -n '1085,1145p' $AUDIO_PY
echo ""
echo "=== 2. compress_audio 定义 ==="
grep -n "def compress_audio" $AUDIO_PY
LINE=$(grep -n "def compress_audio" $AUDIO_PY | head -1 | cut -d: -f1)
if [ -n "$LINE" ]; then
  sed -n "${LINE},$((LINE+30))p" $AUDIO_PY
fi
echo ""
echo "=== 3. transcription 端点（1185-1215行） ==="
sed -n '1185,1215p' $AUDIO_PY
echo ""
echo "=== 4. transcription_handler 开头（880-916行完整） ==="
sed -n '880,916p' $AUDIO_PY
