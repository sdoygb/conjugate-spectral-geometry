#!/bin/bash
echo "=== 1. open-webui 进程实际环境变量中的代理（最直接） ==="
echo 'ab640815.' | sudo -S cat /proc/9938/environ 2>/dev/null | tr '\0' '\n' | grep -iE "proxy|no_proxy" 
echo "--- 若上面为空，说明进程无代理变量 ---"
echo ""
echo "=== 2. systemd 全局环境 ==="
systemctl show-environment 2>/dev/null | head -10
echo ""
echo "=== 3. /etc/environment ==="
cat /etc/environment 2>/dev/null
echo ""
echo "=== 4. 当前 SSH 会话的代理（对照） ==="
env | grep -iE "proxy" || echo "（SSH 会话无代理）"
echo ""
echo "=== 5. 最近进程（确认 PID 是否还是 9938） ==="
systemctl show open-webui --property=MainPID 2>/dev/null
