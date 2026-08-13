#!/bin/bash
echo "=== 1. 最新日志（30分钟） ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "30 min ago" --no-pager 2>/dev/null | grep -iE "transcrib|422|ffprobe|ffmpeg|audio|chunk|stt|wav" | tail -40
echo ""
echo "=== 2. Open WebUI 安装位置 ==="
find /usr/local/geometry-ai -maxdepth 7 -type d -name "open_webui" 2>/dev/null | head -3
echo ""
echo "=== 3. 最近的临时音频文件 ==="
find /tmp -maxdepth 2 -type f \( -name "*.wav" -o -name "*.webm" -o -name "*.ogg" -o -name "*.mp4" -o -name "*.m4a" -o -name "*.opus" \) -mmin -30 2>/dev/null | head -10
echo "--- /tmp 最近修改的文件 ---"
ls -lt /tmp/ 2>/dev/null | head -25
echo ""
echo "=== 4. Open WebUI 音频处理代码位置 ==="
find /usr/local/geometry-ai -path "*open_webui*" -name "utils.py" 2>/dev/null | grep -i audio | head -5
find /usr/local/geometry-ai -path "*open_webui*audio*" -name "*.py" 2>/dev/null | head -10
