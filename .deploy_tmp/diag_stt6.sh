#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo "=== 1. _transcribe_openai 完整代码（655-715行） ==="
sed -n '655,715p' $AUDIO_PY
echo ""
echo "=== 2. transcription_handler（880-930行） ==="
sed -n '880,930p' $AUDIO_PY
echo ""
echo "=== 3. transcribe（1040-1085行） ==="
sed -n '1040,1085p' $AUDIO_PY
echo ""
echo "=== 4. convert_audio_to_mp3（150-185行） ==="
sed -n '150,185p' $AUDIO_PY
echo ""
echo "=== 5. systemd 服务代理环境变量 ==="
systemctl cat open-webui 2>/dev/null | grep -iE "proxy|environment" | head -10
