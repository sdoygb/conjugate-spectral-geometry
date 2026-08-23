#!/bin/bash
# =============================================================================
# GeometryAI 中间层统一管理脚本（替代原 com.geometryai.subai 的 launchd 自动拉起）
# -----------------------------------------------------------------------------
# 用法:
#   ./start-middleware.sh start    启动中间层(app/server.py, 端口 5000, 后台 nohup)
#   ./start-middleware.sh stop     停止中间层
#   ./start-middleware.sh restart  重启中间层
#   ./start-middleware.sh status   查看监听状态与占用 PID
#
# 环境: 复用 ~/.geometryai/secrets.env 的 API 密钥（若存在），并复刻原 launchd
#       配置的 HF_ENDPOINT / SENTENCE_TRANSFORMERS_HOME 等，保证配置与迁移前一致。
# 日志: middleware.log
# =============================================================================
set -euo pipefail

# 关键：清掉外部注入的 PYTHONHOME/PYTHONPATH，避免 python3.11 被沙箱/代理污染
# （污染会导致 init_fs_encoding 失败、No module named 'encodings'）
unset PYTHONHOME PYTHONPATH

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${SCRIPT_DIR}/app"
SECRETS="${HOME:-/Users/oygb}/.geometryai/secrets.env"
LOG_FILE="${SCRIPT_DIR}/middleware.log"
PORT=5000
PY=/usr/local/bin/python3.11

# --- 复原件 launchd 配置的环境，保证与迁移前行为一致 ---
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HOME="${HOME:-/Users/oygb}"
export PYTHONUNBUFFERED=1
export SENTENCE_TRANSFORMERS_HOME="${SCRIPT_DIR}/models_cache"
export RAG_EMBEDDING_MODEL="${RAG_EMBEDDING_MODEL:-BAAI/bge-m3}"
# 密钥（API key / base 等）；若存在则 source，缺省也不报错（留给环境注入）
if [ -f "$SECRETS" ]; then
  # set -a: 声明导出让 python 子进程能读到这些变量
  set -a
  # shellcheck disable=SC1090
  source "$SECRETS"
  set +a
fi

_pid_on_port() {
  lsof -nP -iTCP:${PORT} -sTCP:LISTEN -t 2>/dev/null | head -1 || true
}

_is_running() {
  local p; p="$(_pid_on_port)"
  [ -n "$p" ]
}

do_start() {
  if _is_running; then
    echo "中间层已在运行: PID $(_pid_on_port) (端口 ${PORT})"
    return 0
  fi
  if [ ! -f "${APP_DIR}/server.py" ]; then
    echo "错误: 未找到 ${APP_DIR}/server.py"
    return 1
  fi
  ( cd "${APP_DIR}" && nohup "${PY}" server.py >>"${LOG_FILE}" 2>&1 & )
  # 等待端口就绪（最多 90 秒；首次需加载向量库/模型）
  for i in $(seq 1 90); do
    if _is_running; then break; fi
    sleep 1
  done
  if _is_running; then
    echo "中间层已启动: PID $(_pid_on_port) (端口 ${PORT}) | 日志: ${LOG_FILE}"
  else
    echo "启动超时(90s)或失败，请检查日志: tail -f ${LOG_FILE}"
    return 1
  fi
}

do_stop() {
  local p; p="$(_pid_on_port)"
  if [ -z "$p" ]; then
    echo "中间层未在运行 (端口 ${PORT} 无监听)"
    return 0
  fi
  echo "停止中间层 PID $p ..."
  kill "$p" 2>/dev/null || true
  for i in $(seq 1 15); do
    if ! _is_running; then break; fi
    sleep 1
  done
  p="$(_pid_on_port)"
  if [ -n "$p" ]; then
    echo "未正常退出，强制结束 PID $p"
    kill -9 "$p" 2>/dev/null || true
  fi
  echo "已停止"
}

case "${1:-}" in
  start)   do_start ;;
  stop)    do_stop ;;
  restart) do_stop; sleep 1; do_start ;;
  status)
    if _is_running; then
      echo "运行中: PID $(_pid_on_port) (端口 ${PORT}) | 日志: ${LOG_FILE}"
    else
      echo "未在运行 (端口 ${PORT} 无监听)"
    fi
    ;;
  *)
    echo "用法: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac