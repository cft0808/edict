#!/bin/bash
cd "$(dirname "$0")" || exit 1
PORT=${1:-7891}
echo "軍機處看板 → http://127.0.0.1:$PORT"
pkill -f "http.server $PORT" 2>/dev/null
exec python3 -m http.server "$PORT" --bind 127.0.0.1
