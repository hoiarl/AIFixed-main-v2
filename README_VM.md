# Быстрый запуск на VM (IP 188.120.241.192)

В архив уже добавлены готовые файлы:
- `backend/.env`
- `frontend/.env`
- `backend/init_db.py`

Перед запуском замени в `backend/.env` только 2 вещи:
1. `GIGACHAT_AUTH_KEY=...`
2. `SECRET_KEY=...`

## Вариант 1 — самый простой, без Docker

### 1) Установить системные пакеты
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql postgresql-contrib build-essential libpq-dev
```

### 2) Поднять PostgreSQL и создать БД
```bash
sudo -u postgres psql -c "CREATE USER aifixed WITH PASSWORD 'aifixed123';"
sudo -u postgres psql -c "CREATE DATABASE aifixed OWNER aifixed;"
sudo -u postgres psql -c "ALTER USER aifixed CREATEDB;"
```

### 3) Запустить backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python init_db.py
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 4) Запустить frontend
Во втором терминале:
```bash
cd frontend
npm install
npm start
```

После этого открой:
- Frontend: `http://188.120.241.192:3000`
- Backend docs: `http://188.120.241.192:8000/docs`

## Вариант 2 — чтобы фронт был на 80 порту
После `npm install` можно собрать frontend:
```bash
cd frontend
npm install
npm run build
```

И раздать его через nginx, если нужно. Но для первой проверки удобнее запускать `npm start` на 3000 порту.

## Что проверить
- сайт открывается сразу без логина;
- `/projects` открывается без авторизации;
- генерация презентации работает;
- сохранение презентации работает;
- сохранённые презентации видны в списке.

## Если GigaChat ругается на SSL
Сейчас в `backend/.env` уже стоит `GIGACHAT_VERIFY_SSL=false` для быстрого старта.
Для нормального production-режима установи сертификаты Минцифры и переключи на `true`.
