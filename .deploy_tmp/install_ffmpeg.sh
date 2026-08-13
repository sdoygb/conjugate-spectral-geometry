#!/bin/bash
echo "=== 安装 ffmpeg（apt） ==="
echo 'ab640815.' | sudo -S apt-get install -y ffmpeg 2>&1 | tail -6
echo ""
echo "=== 验证安装 ==="
which ffmpeg ffprobe 2>/dev/null
ffprobe -version 2>/dev/null | head -1
echo ""
echo "=== 模拟 Open WebUI 转换流程：webm → wav ==="
python3 -c "
import wave, struct, math
with wave.open('/tmp/test_pcm16.wav','w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b''.join(struct.pack('<h', int(8000*math.sin(2*math.pi*440*i/16000))) for i in range(16000)))
print('源 wav 已生成')
"
ffmpeg -y -i /tmp/test_pcm16.wav -c:a libopus -b:a 24k /tmp/test_browser.webm 2>&1 | tail -2
echo "--- webm 已生成，现在用 ffprobe 检测并转回 wav（复刻 Open WebUI 逻辑） ---"
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -of default=noprint_wrappers=1 /tmp/test_browser.webm 2>&1
ffmpeg -y -i /tmp/test_browser.webm -ar 16000 -ac 1 -c:a pcm_s16le /tmp/converted.wav 2>&1 | tail -1
ls -la /tmp/converted.wav 2>/dev/null && echo "转换成功 ✅"
