#!/bin/bash
# 三省六部 · 数据刷新循环
# 每 15 秒同步一次所有数据源

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🏛️  三省六部数据刷新循环启动 (PID=$$)"
echo "   脚本目录: $SCRIPT_DIR"
echo "   日志: /tmp/sansheng_liubu_refresh.log"
echo "   按 Ctrl+C 停止"

while true; do
  python3 "$SCRIPT_DIR/sync_from_openclaw_runtime.py" >> /tmp/sansheng_liubu_refresh.log 2>&1
  python3 "$SCRIPT_DIR/sync_agent_config.py"          >> /tmp/sansheng_liubu_refresh.log 2>&1
  python3 "$SCRIPT_DIR/apply_model_changes.py"        >> /tmp/sansheng_liubu_refresh.log 2>&1
  python3 "$SCRIPT_DIR/sync_officials_stats.py"       >> /tmp/sansheng_liubu_refresh.log 2>&1
  python3 "$SCRIPT_DIR/refresh_live_data.py"          >> /tmp/sansheng_liubu_refresh.log 2>&1
  sleep 15
done
