# ЭТО

Социальная сеть с функциями:
- Регистрация и вход
- Лента постов с лайками и комментариями
- Профили пользователей и друзья
- Личные сообщения (чат)
- Истории
- Группы

## Технологии

**Backend:** Python + FastAPI + SQLAlchemy + SQLite
**Frontend:** React + TypeScript + Vite

## Запуск

### Быстрый старт
```bash
chmod +x start.sh
./start.sh
```

Открой http://localhost:5173

### Ручной запуск

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API

API доступно на http://localhost:8000/api/
Документация: http://localhost:8000/docs

## Репозиторий

https://github.com/EBAAAAAAA-sistemnetwork/eto-social-network
