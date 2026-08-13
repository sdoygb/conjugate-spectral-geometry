#!/bin/bash
echo "========== WEBUI 升级脚本 $(date +%F_%T) =========="
echo "=== 1. 备份数据 ==="
DATA=/usr/local/geometry-ai/venv/lib/python3.12/site-packages/open_webui/data
BK=/root/webui_backup_$(date +%Y%m%d%H%M%S)
mkdir -p $BK
cp -a $DATA/. $BK/
echo "备份完成: $BK 大小=$(du -sh $BK 2>/dev/null | cut -f1)"
ls $BK | head -8

echo ""
echo "=== 2. 迁移数据到外部目录 ==="
EXT=/usr/local/geometry-ai/webui_data
mkdir -p $EXT
cp -a $DATA/. $EXT/
echo "外部数据目录: $EXT 大小=$(du -sh $EXT 2>/dev/null | cut -f1)"
ls $EXT | head -8

echo ""
echo "=== 3. 停服务 + 禁用坏服务 ==="
systemctl stop open-webui
systemctl disable geometry-ai-webui 2>&1 | tail -1
systemctl stop geometry-ai-webui 2>/dev/null
echo "open-webui: $(systemctl is-active open-webui), geometry-ai-webui: $(systemctl is-enabled geometry-ai-webui)"

echo ""
echo "=== 4. pip 升级 open-webui ==="
/usr/local/geometry-ai/venv/bin/pip install -U open-webui 2>&1 | tail -8

echo ""
echo "=== 5. 版本确认 ==="
/usr/local/geometry-ai/venv/bin/pip show open-webui | head -2

echo ""
echo "=== 6. 服务文件配置 OPENWEBUI_DATA_DIR ==="
SRV=/etc/systemd/system/open-webui.service
if ! grep -q "OPENWEBUI_DATA_DIR" $SRV; then
  sed -i '/ENABLE_UPDATE_CHECK/a Environment="OPENWEBUI_DATA_DIR=/usr/local/geometry-ai/webui_data"' $SRV
  echo "已插入 OPENWEBUI_DATA_DIR"
fi
grep -n "OPENWEBUI_DATA_DIR" $SRV

echo ""
echo "=== 7. 启动服务 ==="
systemctl daemon-reload
systemctl start open-webui
sleep 8
echo "服务状态: $(systemctl is-active open-webui)"

echo ""
echo "=== 8. 版本 API 验证 ==="
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=8))
    print('版本响应:', r)
except Exception as e:
    print('ERR', type(e).__name__, e)
"

echo ""
echo "=== 9. 数据完整性检查 ==="
ls -la /usr/local/geometry-ai/webui_data/ | head -12
echo "========== 升级脚本结束 $(date +%F_%T) =========="
