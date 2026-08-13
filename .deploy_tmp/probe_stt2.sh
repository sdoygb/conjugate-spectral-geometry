#!/bin/bash
echo "=== 1. 系统信息与 ffmpeg ==="
cat /etc/os-release 2>/dev/null | grep -E "^(ID|VERSION_ID|PRETTY_NAME)=" | head -3
which ffmpeg ffprobe 2>/dev/null || echo "（未安装 ffmpeg/ffprobe）"
echo ""
echo "=== 2. 只读查 webui.db STT 配置 ==="
python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
try:
    cur.execute(\"SELECT key, value FROM config WHERE key LIKE '%stt%' OR key LIKE '%audio%'\")
    for k, v in cur.fetchall():
        if 'key' in k.lower() or 'token' in k.lower():
            print(f'{k} = sk-***' if v and len(v) > 6 else f'{k} = (空)')
        else:
            print(f'{k} = {v}')
except Exception as e:
    print('查询失败:', e)
conn.close()
"
echo ""
echo "=== 3. 实测 SiliconFlow STT：标准 PCM16 wav + SenseVoiceSmall ==="
python3 -c "
import wave, struct, math
with wave.open('/tmp/test_pcm16.wav','w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b''.join(struct.pack('<h', int(8000*math.sin(2*math.pi*440*i/16000))) for i in range(16000)))
print('已生成 /tmp/test_pcm16.wav (16kHz 16bit PCM 单声道 1秒)')
"
KEY=$(grep -E "^SILICONFLOW_API_KEY" /usr/local/geometry-ai/.env 2>/dev/null | head -1 | cut -d= -f2-)
echo "--- POST /v1/audio/transcriptions (model=FunAudioLLM/SenseVoiceSmall) ---"
curl -s --max-time 30 -X POST https://api.siliconflow.cn/v1/audio/transcriptions \
  -H "Authorization: Bearer $KEY" \
  -F "file=@/tmp/test_pcm16.wav" \
  -F "model=FunAudioLLM/SenseVoiceSmall" | head -c 600
echo ""
