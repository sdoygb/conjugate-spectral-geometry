#!/bin/bash
CACHE="/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions"
echo "=== 1. 最近的缓存音频文件 ==="
echo 'ab640815.' | sudo -S ls -lat $CACHE 2>/dev/null | head -12
echo ""
echo "=== 2. ffprobe 检测最新 mp3 ==="
LATEST_MP3=$(echo 'ab640815.' | sudo -S ls -t $CACHE/*.mp3 2>/dev/null | head -1)
echo "最新 mp3: $LATEST_MP3"
echo 'ab640815.' | sudo -S ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,bit_rate,duration -of json "$LATEST_MP3" 2>&1 | head -20
echo ""
echo "=== 3. 文件大小 ==="
echo 'ab640815.' | sudo -S ls -la "$LATEST_MP3" 2>/dev/null
echo ""
echo "=== 4. 当前 STT 配置（db 只读） ==="
echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT key, value FROM config WHERE key LIKE '%audio%' OR key LIKE '%stt%'\")
for k, v in cur.fetchall():
    if 'key' in k.lower() and v and len(v) > 8:
        print(f'{k} = sk-***')
    else:
        print(f'{k} = {v}')
conn.close()
" 2>&1 | head -30
echo ""
echo "=== 5. 用该 mp3 实测 SiliconFlow ==="
KEY=$(grep -E "^SILICONFLOW_API_KEY" /usr/local/geometry-ai/.env | head -1 | cut -d= -f2-)
MODEL=$(echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT value FROM config WHERE key='audio.stt.model' OR key LIKE '%audio.stt.model%' LIMIT 1\")
r = cur.fetchone()
print(r[0] if r else 'FunAudioLLM/SenseVoiceSmall')
conn.close()
" 2>/dev/null | tail -1)
echo "配置模型: $MODEL"
echo 'ab640815.' | sudo -S cp "$LATEST_MP3" /tmp/test_latest.mp3 2>/dev/null
echo 'ab640815.' | sudo -S chmod 644 /tmp/test_latest.mp3
curl -s --max-time 30 -X POST https://api.siliconflow.cn/v1/audio/transcriptions \
  -H "Authorization: Bearer $KEY" \
  -F "file=@/tmp/test_latest.mp3;type=audio/mpeg" \
  -F "model=$MODEL" | head -c 1000
echo ""
