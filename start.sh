#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "===================================="
echo "  ЭТО — Социальная сеть"
echo "===================================="
echo ""

# Backend
echo "Запуск backend..."
cd "$SCRIPT_DIR/backend"
python3 -m pip install -r requirements.txt -q 2>/dev/null || echo "(зависимости уже установлены)"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend: http://localhost:8000 (PID: $BACKEND_PID)"
echo "  API docs: http://localhost:8000/docs"

# Frontend
echo "Запуск frontend..."
cd "$SCRIPT_DIR/frontend"
npm install --silent 2>/dev/null || echo "(зависимости уже установлены)"
npm run dev -- --host &
FRONTEND_PID=$!
echo "  Frontend: http://localhost:5173"

echo ""
echo "===================================="
echo "  Открой http://localhost:5173"
echo "  Нажми Ctrl+C чтобы остановить"
echo "===================================="
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Остановлено'" EXIT
wait
