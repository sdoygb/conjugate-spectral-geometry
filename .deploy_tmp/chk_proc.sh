#!/bin/bash
echo '=== 进程 14382 实际环境变量(DATA相关) ==='
echo 'ab640815.' | sudo -S cat /proc/14382/environ 2>/dev/null | tr '\0' '\n' | grep -iE 'OPENWEBUI|DATA_DIR|WEBUI'
echo '(空=读不到)'
echo
echo '=== 进程 14382 打开的文件(db/data) ==='
echo 'ab640815.' | sudo -S ls -l /proc/14382/fd 2>/dev/null | grep -iE 'webui|data|\.db' | head -15
echo
echo '=== 进程工作目录 ==='
echo 'ab640815.' | sudo -S ls -l /proc/14382/cwd 2>/dev/null
echo
echo '=== systemd 加载的 unit 与磁盘 unit 是否一致 ==='
systemctl show open-webui --property=Environment 2>/dev/null | tr ' ' '\n' | grep -i data
