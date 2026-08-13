#!/bin/bash
PID=$(systemctl show open-webui -p MainPID --value)
echo 'PID='$PID
echo '=== fd webui/data ==='
echo 'ab640815.' | sudo -S ls -l /proc/$PID/fd 2>/dev/null | grep -iE 'webui|data|db' | head -8
echo '=== pkg cache ==='
ls -la /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/ 2>&1 | head -8
echo '=== geo cache ==='
ls -la /usr/local/geometry-ai/webui_data/cache/audio/transcriptions/ 2>&1 | head -8
echo '=== tmp audio ==='
ls -la /tmp/*.mp3 /tmp/*.wav 2>&1 | head -6
echo '=== db mtime ==='
stat -c '%y %n' /usr/local/geometry-ai/webui_data/webui.db /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db 2>&1
echo '=== geo db stt ==='
sqlite3 /usr/local/geometry-ai/webui_data/webui.db "select data from config where id='audio.stt.openai'" 2>&1 | head -c 300
echo
echo '=== pkg db stt ==='
sqlite3 /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db "select data from config where id='audio.stt.openai'" 2>&1 | head -c 300
echo
echo '=== done ==='
