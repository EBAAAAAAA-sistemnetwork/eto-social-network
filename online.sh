#!/bin/bash
echo 'ЭТО — социальная сеть'
echo 'Запуск...'

# Kill old tunnel
pkill -f 'ssh.*serveo.net' 2>/dev/null

# Check if backend is running
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo 'Запускаю backend...'
    PATH="/Users/vladimir/Library/Python/3.9/bin:$PATH"
    cd /Users/vladimir/Desktop/opencode/ADC4/social-network/backend
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
    sleep 2
    echo 'Backend запущен'
fi

echo 'Создаю туннель в интернет...'
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -R 80:localhost:8000 serveo.net

echo 'Туннель закрыт'