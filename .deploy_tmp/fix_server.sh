#!/bin/bash
# 修复脚本 v2：1.备份损坏chroma_db(容错) 2.补.env多模型配置(sudo tee) 3.重启服务
set -e
echo "=== 1. 备份损坏 chroma_db ==="
if [ -d /usr/local/geometry-ai/chroma_db ]; then
    BK=/usr/local/geometry-ai/chroma_db_broken_$(date +%Y%m%d%H%M%S)
    sudo mv /usr/local/geometry-ai/chroma_db "$BK"
    echo "已备份: $BK"
else
    echo "chroma_db 已不存在（可能已备份），现有备份:"
    ls -d /usr/local/geometry-ai/chroma_db_broken_* 2>/dev/null || echo "无备份记录"
fi

echo "=== 2. 补充 .env 多模型配置 ==="
ENV=/usr/local/geometry-ai/.env
if ! grep -q "PROVIDER_gpt" "$ENV" 2>/dev/null; then
    sudo tee -a "$ENV" > /dev/null <<'CONF'

# ==================== 多模型提供商 ====================
GAI_MODEL_VISION=kimi-k2.6
GAI_LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
PROVIDER_gpt=https://oa.api2d.net/v1,fk245651-kMlfPs4v2nL6AMNjHFRVWr3hcL0SzZU1
PROVIDER_claude=https://oa.api2d.net/v1,fk245651-kMlfPs4v2nL6AMNjHFRVWr3hcL0SzZU1
PROVIDER_kimi=https://api.moonshot.cn/v1,sk-gSmPVYGo8t43kRlBjLxp61E2L44KrLpPtPoJrIYy6EJN3idO
EXTRA_MODELS=gpt-5.4,gpt-5.4-mini,claude-opus-4-20250514,claude-sonnet-4-20250514,kimi-k3,kimi-k2.7-code,kimi-k2.6
CONF
    echo ".env 已追加多模型配置"
else
    echo ".env 已包含 PROVIDER_gpt，跳过追加"
fi
echo ".env 配置行数: $(grep -cE '^PROVIDER_|^EXTRA_MODELS|^GAI_MODEL_VISION|^GAI_LOCAL_EMBEDDING' "$ENV")"

echo "=== 3. 重启服务 ==="
sudo systemctl restart geometry-ai
sleep 10
echo "服务状态: $(systemctl is-active geometry-ai)"

echo "=== 4. 启动日志 ==="
journalctl -u geometry-ai --no-pager -n 40 | grep -E "STARTUP|VECTOR|ERROR" | tail -20
echo "=== 修复脚本执行完毕 ==="
