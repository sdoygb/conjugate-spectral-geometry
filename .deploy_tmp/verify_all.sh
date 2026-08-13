#!/bin/bash
echo '=== uptime ==='
uptime
echo '=== services ==='
systemctl is-active open-webui geometry-ai nginx
echo '=== open-webui pid/time ==='
systemctl show open-webui -p MainPID -p ActiveEnterTimestamp
echo '=== geometry-ai pid/time ==='
systemctl show geometry-ai -p MainPID -p ActiveEnterTimestamp
echo '=== port 8080 ==='
ss -tlnp 2>/dev/null | grep 8080
echo '=== open-webui startup errors ==='
journalctl -u open-webui --since '4 min ago' --no-pager 2>/dev/null | grep -iE 'error|traceback|failed' | head -10
echo '=== geometry-ai startup errors ==='
journalctl -u geometry-ai --since '4 min ago' --no-pager 2>/dev/null | grep -iE 'error|traceback|failed' | head -10
echo '=== nginx status ==='
systemctl status nginx --no-pager 2>/dev/null | head -4
echo '=== open-webui db in use ==='
PID=$(systemctl show open-webui -p MainPID --value)
echo 'ab640815.' | sudo -S ls -l /proc/$PID/fd 2>/dev/null | grep -iE 'webui|data' | head -8
echo '=== health check ==='
python3 -c "import urllib.request; print('health:', urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=10).status)" 2>&1
echo '=== chroma/articles ==='
ls /usr/local/geometry-ai/chroma_db 2>/dev/null | head -5
ls /usr/local/geometry-ai/articles 2>/dev/null | head -5
echo '=== done ==='
