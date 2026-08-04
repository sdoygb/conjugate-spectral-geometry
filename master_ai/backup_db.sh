#!/bin/bash
# 主库AI ChromaDB 自动备份脚本
# 备份到 ~/GeometryAI_backups（不受TCC限制），保留最近7天

SOURCE_DB="/Users/oygb/Downloads/GeometryAI-Mac-Build/master_ai/master_chroma_db"
BACKUP_DIR="${HOME}/GeometryAI_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/chroma_${DATE}"

mkdir -p "${BACKUP_DIR}"

# 检查源数据库
if [ ! -f "${SOURCE_DB}/chroma.sqlite3" ]; then
    echo "[$(date)] 错误: 源数据库不存在"
    exit 1
fi

# 统计embedding数量
COUNT=$(sqlite3 "${SOURCE_DB}/chroma.sqlite3" "SELECT count(*) FROM embeddings;" 2>/dev/null || echo "0")

if [ "$COUNT" -gt "0" ]; then
    cp -r "${SOURCE_DB}" "${BACKUP_PATH}"
    echo "[$(date)] 备份成功: ${BACKUP_PATH} (${COUNT} 条embedding)"
else
    echo "[$(date)] 跳过备份: 数据库为空 (0 条embedding)"
    exit 0
fi

# 清理7天前的备份
find "${BACKUP_DIR}" -name "chroma_*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null

# 报告最新备份
LATEST=$(ls -td "${BACKUP_DIR}/chroma_"* 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    LCOUNT=$(sqlite3 "${LATEST}/chroma.sqlite3" "SELECT count(*) FROM embeddings;" 2>/dev/null || echo "0")
    echo "[$(date)] 最新备份: ${LATEST} (${LCOUNT} 条embedding)"
fi
