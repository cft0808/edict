#!/bin/bash
# 三省六部 · 数据刷新循环
# 用法: ./run_loop.sh [间隔秒数]  (默认 15)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERVAL="${1:-15}"
LOG="/tmp/sansheng_liubu_refresh.log"
PIDFILE="/tmp/sansheng_liubu_refresh.pid"
MAX_LOG_SIZE=$((10 * 1024 * 1024))  # 10MB

# ── 单实例保护 ──
if [[ -f "$PIDFILE" ]]; then
  OLD_PID=$(cat "$PIDFILE" 2>/dev/null)
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "❌ 已有实例运行中 (PID=$OLD_PID)，退出"
    exit 1
  fi
  rm -f "$PIDFILE"
fi
echo $$ > "$PIDFILE"

# ── 优雅退出 ──
cleanup() {
  echo "$(date '+%H:%M:%S') [loop] 收到退出信号，清理中..." >> "$LOG"
  rm -f "$PIDFILE"
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# ── 日志轮转 ──
rotate_log() {
  if [[ -f "$LOG" ]] && (( $(stat -f%z "$LOG" 2>/dev/null || stat -c%s "$LOG" 2>/dev/null || echo 0) > MAX_LOG_SIZE )); then
    mv "$LOG" "${LOG}.1"
    echo "$(date '+%H:%M:%S') [loop] 日志已轮转" > "$LOG"
  fi
}

echo "🏛️  三省六部数据刷新循环启动 (PID=$$)"
echo "   脚本目录: $SCRIPT_DIR"
echo "   间隔: ${INTERVAL}s"
echo "   日志: $LOG"
echo "   PID文件: $PIDFILE"
echo "   按 Ctrl+C 停止"

while true; do
  rotate_log
  python3 "$SCRIPT_DIR/sync_from_openclaw_runtime.py" >> "$LOG" 2>&1 || true
  python3 "$SCRIPT_DIR/sync_agent_config.py"          >> "$LOG" 2>&1 || true
  python3 "$SCRIPT_DIR/apply_model_changes.py"        >> "$LOG" 2>&1 || true
  python3 "$SCRIPT_DIR/sync_officials_stats.py"       >> "$LOG" 2>&1 || true
  python3 "$SCRIPT_DIR/refresh_live_data.py"          >> "$LOG" 2>&1 || true
  sleep "$INTERVAL"
done
