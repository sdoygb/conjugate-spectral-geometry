#!/bin/bash
echo "=== 1. systemd 服务 ==="
systemctl list-units --type=service --all | grep -iE "webui" || echo "无 webui systemd 服务"
echo ""
echo "=== 2. systemd 服务文件 ==="
for f in /etc/systemd/system/open-webui.service /etc/systemd/system/geometry-ai-webui.service /etc/systemd/system/openwebui.service; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    cat "$f"
  fi
done
echo ""
echo "=== 3. docker 容器 ==="
docker ps -a 2>/dev/null | grep -iE "webui|open" || echo "无 webui 容器或 docker 不可用"
echo ""
echo "=== 4. pip 包 ==="
pip3 show open-webui 2>/dev/null | head -3
/usr/local/geometry-ai/venv/bin/pip show open-webui 2>/dev/null | head -3
python3 -c "import open_webui; print('open_webui', open_webui.__version__)" 2>/dev/null || echo "python3 无 open_webui"
echo ""
echo "=== 5. 端口监听 ==="
ss -tlnp 2>/dev/null | grep -E ":3000|:8080" || echo "无 3000/8080 监听"
echo ""
echo "=== 6. 相关目录 ==="
ls -d /opt/open-webui /root/open-webui /home/sdoygb/open-webui /usr/local/open-webui /app/backend 2>/dev/null || echo "无常见目录"
