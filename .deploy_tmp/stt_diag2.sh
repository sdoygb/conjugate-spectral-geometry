#!/bin/bash
echo "=== 1. 最新 STT 相关日志（30 分钟） ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "30 min ago" --no-pager 2>/dev/null | grep -iE "transcrib|stt|audio|ffprobe|ffmpeg|422|error|wav" | tail -40
echo ""
echo "=== 2. 查找最近的音频文件 ==="
find /usr/local/geometry-ai/webui_data -type f \( -name "*.wav" -o -name "*.webm" -o -name "*.mp4" -o -name "*.ogg" -o -name "*.opus" -o -name "*.m4a" \) -mmin -120 2>/dev/null | head -15
echo ""
echo "=== 3. 音频缓存目录 ==="
ls -lat /usr/local/geometry-ai/webui_data/cache/audio/ 2>/dev/null | head -10
echo "---"
ls -lat /usr/local/geometry-ai/webui_data/cache/ 2>/dev/null | head -15
echo ""
echo "=== 4. ffprobe 当前可用性 ==="
which ffprobe ffmpeg
ffprobe -version 2>/dev/null | head -1
