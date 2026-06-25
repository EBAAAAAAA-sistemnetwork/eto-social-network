#!/bin/bash
echo "========================================"
echo "       ЭТО — Социальная сеть"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND=$!
sleep 2

ssh -o ServerAliveInterval=60 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -R 80:localhost:8000 serveo.net 2>&1 | while read line; do
    echo "$line"
done &
TUNNEL=$!
sleep 5

echo ""
echo "========================================"
echo "  Сайт запущен!"
echo "  Для ссылки смотри выше ↑"
echo "  Ctrl+C — остановить"
echo "========================================"

trap "kill $BACKEND $TUNNEL 2>/dev/null; exit" INT TERM
wait