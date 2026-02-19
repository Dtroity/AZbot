# Инструкция по продакшен-деплою бота на VPS

Пошаговое руководство по развёртыванию Supply Management System (Telegram-бот + API + Dashboard) на VPS.

---

## 1. Требования к VPS

- **ОС:** Ubuntu 22.04 LTS (рекомендуется) или Debian 12
- **Ресурсы:** минимум 2 GB RAM, 2 vCPU, 20 GB SSD
- **Порты:** 80, 443 (веб), при необходимости 22 (SSH)

---

## 2. Подготовка сервера

### 2.1 Обновление и базовые пакеты

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
```

### 2.2 Установка Docker и Docker Compose

```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Выйти и зайти по SSH заново, чтобы группа применилась

# Docker Compose (plugin)
sudo apt install -y docker-compose-plugin
docker compose version
```

---

## 3. Клонирование и настройка проекта

### 3.1 Клонирование репозитория

```bash
cd /opt  # или другой каталог
sudo git clone https://github.com/YOUR_USER/AZbot.git
cd AZbot
sudo chown -R $USER:$USER .
```

### 3.2 Файл окружения `.env`

Создайте `.env` в корне проекта (рядом с `docker-compose.yml`):

```bash
cp .env.example .env
nano .env
```

**Обязательно задайте:**

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) | `7123456789:AAH...` |
| `ADMINS` | Telegram ID админов через запятую, без пробелов | `123456789,987654321` |
| `SECRET_KEY` | Секрет для API (сложная строка) | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Пароль БД (в продакшене смените) | не оставляйте `postgres` |

**Для продакшена в `.env` должны быть:**

- `DEBUG=false`
- `POSTGRES_HOST=db` (в Docker уже подставится из compose)
- `REDIS_HOST=redis`
- Для доступа к Dashboard по домену: `REACT_APP_API_URL=https://yourdomain.com/api` (см. п. 7)

**Важно:** В `bot/config.py` поле читается как `bot_token` — Pydantic берёт значение из переменной `BOT_TOKEN` автоматически. Поле `admins` парсится из строки `ADMINS` (через запятую). Убедитесь, что в `ADMINS` только числа, без пробелов: `123,456`.

---

## 4. Исправление известных проблем перед деплоем

### 4.1 Клавиатуры (импорты)

Если в логах бота есть ошибка про `supplier_management_keyboard`:

- Проверьте `bot/handlers/admin.py`: импортируйте только то, что реально есть в `bot/keyboards/__init__.py` (`order_keyboard`, `order_status_keyboard`, `admin_keyboard`).
- Либо добавьте в `bot/keyboards/__init__.py` экспорт `supplier_management_keyboard`, если такая клавиатура есть в `bot/keyboards/admin.py`.

### 4.2 Dashboard: package-lock.json

Сборка Dashboard использует `npm ci`, которому нужен `package-lock.json`:

```bash
cd dashboard
npm install
# Будет создан package-lock.json
cd ..
git add dashboard/package-lock.json
git commit -m "Add package-lock.json for dashboard build"
```

Без этого шага образ Dashboard не соберётся.

### 4.3 Версия docker-compose

В `docker-compose.yml` указано `version: "3.9"`. Для Docker Compose V2 плагина поле `version` необязательно — можно оставить или обновить до актуальной схемы при необходимости.

---

## 5. Запуск сервисов

### 5.1 Запуск всех контейнеров

```bash
cd /opt/AZbot   # или ваш путь
docker compose up -d
```

Проверка статуса:

```bash
docker compose ps
```

Должны быть в состоянии **Up**: `supply_db`, `supply_redis`, `supply_api`, `supply_bot`. Dashboard и nginx — по желанию (см. ниже).

### 5.2 Инициализация базы данных

Таблицы создаются через SQLAlchemy. Выполните один раз после первого запуска:

```bash
docker compose exec api python -c "
from api.database import init_db
import asyncio
asyncio.run(init_db())
print('Database initialized.')
"
```

Либо из контейнера бота (если у него есть доступ к той же БД и модели):

```bash
docker compose exec bot python -c "
from db.models import Base
from bot.database import engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
print('Database initialized.')
"
```

Проверка: зайдите в БД и убедитесь, что таблицы созданы:

```bash
docker compose exec db psql -U postgres -d supply -c '\dt'
```

---

## 6. Проверка работы бота

- Логи бота:  
  `docker compose logs -f bot`
- Перезапуск бота:  
  `docker compose restart bot`
- Проверка API:  
  `curl http://localhost:8000/health` (с сервера) или с вашего ПК по IP:8000, если порт открыт.

Если бот не стартует из-за импорта — исправьте импорты клавиатур (п. 4.1) и пересоберите образ:

```bash
docker compose build bot --no-cache
docker compose up -d bot
```

---

## 7. Dashboard (опционально)

- Создайте `package-lock.json` (п. 4.2), затем:  
  `docker compose build dashboard --no-cache`  
  `docker compose up -d dashboard`
- Для доступа по домену в `.env` задайте:  
  `REACT_APP_API_URL=https://your-domain.com/api`  
  и пересоберите образ dashboard (переменные вшиваются в сборку).

---

## 8. Nginx и SSL (продакшен)

- Положите сертификаты в `nginx/ssl/`:
  - `cert.pem` (или полная цепочка)
  - `key.pem`
- В `nginx/nginx.conf` раскомментируйте блоки:
  - сервер `listen 443 ssl http2`
  - редирект с HTTP на HTTPS (порт 80 → 301 на https)
- В `docker-compose.yml` для nginx при необходимости добавьте volume с сертификатами (уже смонтирован `./nginx/ssl`).
- Перезапуск:  
  `docker compose restart nginx`

Для бесплатного SSL можно использовать certbot (отдельно на хосте или в отдельном контейнере) и подставить выданные им `fullchain.pem` и `privkey.pem` в `nginx/ssl/`.

---

## 9. Автозапуск и перезапуск при сбоях

Docker Compose с `restart: unless-stopped` уже перезапускает контейнеры при падении и после перезагрузки сервера. Убедитесь, что compose поднимается при загрузке:

```bash
# Проверить, что сервис docker включён
sudo systemctl enable docker
sudo systemctl status docker
```

При необходимости можно оформить systemd unit для `docker compose up -d` в нужной директории — тогда всё поднимется после перезагрузки даже без логина.

---

## 10. Мониторинг и логи

- Все сервисы:  
  `docker compose logs -f`
- Только бот:  
  `docker compose logs -f bot`
- Только API:  
  `docker compose logs -f api`
- Логи приложения бота (если пишутся в файл): каталог `./logs`, смонтированный в контейнер бота.

Рекомендуется настроить ротацию логов Docker и при необходимости сбор логов (например, в файлы или внешнюю систему).

---

## 11. Обновление проекта на VPS

```bash
cd /opt/AZbot
git pull
docker compose build --no-cache   # при изменении кода или Dockerfile
docker compose up -d
# При изменении моделей БД — повторить инициализацию или миграции (п. 5.2)
```

---

## 12. Краткий чеклист продакшена

- [ ] VPS с Docker и Docker Compose
- [ ] Репозиторий склонирован, задан владелец каталога
- [ ] `.env` создан из `.env.example`, заданы `BOT_TOKEN`, `ADMINS`, `SECRET_KEY`, надёжный `POSTGRES_PASSWORD`
- [ ] Исправлены импорты клавиатур в боте (при необходимости)
- [ ] В `dashboard` есть `package-lock.json`, образ dashboard собирается
- [ ] `docker compose up -d` выполнен, все нужные контейнеры Up
- [ ] База данных инициализирована (таблицы созданы)
- [ ] Бот запускается без ошибок импорта, отвечает в Telegram
- [ ] API отвечает на `/health`
- [ ] (Опционально) Dashboard собран и доступен
- [ ] (Опционально) Nginx настроен, SSL включён, `REACT_APP_API_URL` указывает на продакшен API

После выполнения этих шагов бот и остальные сервисы готовы к работе на VPS в продакшене.
