#!/usr/bin/env bash
# Полная переустановка БД на VPS. Пароль БД зафиксирован в docker-compose (postgres), том пересоздаётся.
# Запуск из корня проекта: bash scripts/vps-full-reset.sh
# Требует: docker compose, curl

set -e
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"

echo "=== Каталог проекта: $PROJECT_DIR ==="

# 1. Файл .env обязателен для bot/api (BOT_TOKEN, ADMINS, SECRET_KEY)
if [ ! -f .env ]; then
  echo "Создаю .env из .env.example..."
  cp .env.example .env
  echo "Заполните BOT_TOKEN, ADMINS, SECRET_KEY в .env и снова запустите скрипт."
  exit 1
fi

echo "Пароль БД задаётся в docker-compose (postgres), не в .env."

# 3. Остановить контейнеры
echo "=== Останавливаю контейнеры ==="
docker compose down

# 4. Удалить том PostgreSQL (данные БД будут потеряны)
VOL_NAME=$(docker volume ls -q | grep postgres_data | head -1)
if [ -n "$VOL_NAME" ]; then
  echo "Удаляю том: $VOL_NAME"
  docker volume rm "$VOL_NAME"
else
  echo "Том postgres_data не найден (уже удалён или первый запуск)."
fi

# 5. Запуск сервисов (БД инициализируется с паролем postgres из docker-compose)
echo "=== Запускаю сервисы ==="
docker compose up -d

# 6. Ждём готовности БД
echo "Ожидание готовности БД (20 сек)..."
sleep 20

# 7. Создание таблиц
echo "=== Инициализация таблиц БД ==="
docker compose exec -T api python -c "from api.database import init_db; import asyncio; asyncio.run(init_db()); print('OK')" || {
  echo "Ошибка инициализации через api. Пробую через bot..."
  docker compose exec -T bot python -c "
from bot.database import init_db
import asyncio
asyncio.run(init_db())
print('OK')
" || { echo "Ошибка init_db. Проверьте логи: docker compose logs db api bot"; exit 1; }
}

# 8. Проверка API
echo "=== Проверка API ==="
READY=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ready 2>/dev/null || echo "000")
if [ "$READY" = "200" ]; then
  echo "API готов: $(curl -s http://localhost:8000/ready)"
else
  echo "API не готов (код $READY). Проверьте: docker compose logs api"
fi

# 9. Перезапуск бота и API (подхват подключения)
docker compose restart bot api
echo "Перезапущены bot и api."

echo ""
echo "=== Готово. Проверка: docker compose logs -f bot ==="
