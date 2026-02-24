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
| `POSTGRES_PASSWORD` | Не обязателен: пароль БД задаётся в `docker-compose.yml` | можно не указывать |

**Для продакшена в `.env` должны быть:**

- `DEBUG=false`
- `POSTGRES_HOST=db` (в Docker уже подставится из compose)
- `REDIS_HOST=redis`
- Для доступа к Dashboard по домену: `REACT_APP_API_URL=https://yourdomain.com/api` (см. п. 7)

**Важно:** В `bot/config.py` поле читается как `bot_token` — Pydantic берёт значение из переменной `BOT_TOKEN` автоматически. Поле `admins` парсится из строки `ADMINS` (через запятую). Убедитесь, что в `ADMINS` только числа, без пробелов: `123,456`.

**Пароль БД:** В текущем `docker-compose.yml` пароль задан явно как `postgres` для db, bot и api (не из `.env`). Менять только при полном сбросе тома БД (см. п. 4.1).

### 3.3 Пароль для доступа в дашборд

Доступ к дашборду защищён **HTTP Basic Auth** (логин и пароль запрашиваются браузером при открытии страницы).

**Важно:** пароль запрашивается только при входе **через nginx** (порт **80** или **443**). Если открывать дашборд по порту **3000** напрямую (контейнер dashboard), защита не срабатывает. Рекомендуется заходить по адресу с портом 80, например: `http://ВАШ_IP/` или `https://ваш-домен.ru/`.

1. В репозитории уже есть файл **`nginx/htpasswd`** с логином **admin** и паролем **admin**. После `git pull` он подхватится автоматически. Обязательно смените пароль в продакшене (см. п. 2). Если ранее создавали свой `htpasswd`, после обновления он может быть заменён на файл из репозитория — задайте пароль заново.

2. **Задать свой пароль** (пересоздать `nginx/htpasswd`):
   ```bash
   docker run --rm -v $(pwd)/nginx:/out httpd:alpine htpasswd -cb /out/htpasswd admin YOUR_PASSWORD
   ```
   Вместо `admin` и `YOUR_PASSWORD` подставьте нужные логин и пароль.

3. После изменения `nginx/htpasswd` перезапустите nginx:
   ```bash
   docker compose restart nginx
   ```

Файл `nginx/htpasswd` не коммитится в репозиторий (указан в `.gitignore`). При первом деплое скопируйте `htpasswd.example` в `htpasswd`, как в п. 1.

### 3.4 После обновления на сервере (перед выходом из консоли)

После `git pull` выполните по порядку:

1. **Перезапустить контейнеры** (подхват нового `docker-compose.yml` и образов):
   ```bash
   cd ~/AZbot   # или ваш путь к проекту
   docker compose up -d --build
   ```

2. **Проверить, что API отвечает:**
   ```bash
   curl -s http://localhost:8000/ready
   ```
   Ожидается ответ вроде `{"status":"ready","database":"ok"}` и код 200. Если 503 или ошибка — смотрите п. 4.1 (БД) и логи: `docker compose logs api --tail 30`.

3. **Кратко глянуть логи бота** (без ошибок подключения к БД):
   ```bash
   docker compose logs bot --tail 20
   ```

4. **Если обновляли только код (без смены пароля/тома БД)** — пунктов 1–3 достаточно. **Если делали полный сброс БД** — скрипт `vps-full-reset.sh` уже выполняет инициализацию и проверку; после него достаточно убедиться, что `curl .../ready` возвращает OK.

5. **Если в обновлении добавлена защита дашборда паролем** — создайте `nginx/htpasswd` из `nginx/htpasswd.example` (см. п. 3.3) и перезапустите nginx: `docker compose restart nginx`.

После этих проверок можно выходить из консоли.

---

## 4. Исправление известных проблем перед деплоем

### 4.1 Ошибка «password authentication failed for user "postgres"» (бот / API)

Бот или API не могут подключиться к PostgreSQL: пароль, с которым подключаются клиенты, не совпадает с паролем, под которым была инициализирована БД в томе.

**Сейчас в проекте:** пароль зафиксирован в `docker-compose.yml` как **`postgres`** для сервисов db, bot и api (без переменных из .env). Том БД при первом запуске создаётся с этим паролем; при перезапусках пароль не «теряется». Если том был создан раньше с другим паролем — нужен полный сброс (удаление тома и повторный подъём).

**Важно по безопасности:** в логах БД могли появляться попытки выполнить вредоносный SQL (скачивание скрипта с внешнего IP). Это возможно, только если порт PostgreSQL (5432) был открыт в интернет. В текущем `docker-compose.yml` порт 5432 **не пробрасывается** на хост — к БД подключаются только контейнеры по внутренней сети. После обновления и перезапуска убедитесь, что в секции `db` нет `ports: - "5432:5432"`.

#### Окончательное решение (раз и навсегда)

Пересоздать том БД и поднять сервисы заново. Пароль будет один и тот же для db, bot и api (задан в compose).

**Способ 1 — скрипт (рекомендуется):**

На VPS в каталоге проекта выполните:

```bash
cd ~/AZbot
# или: cd /opt/AZbot  — ваш путь к репозиторию

bash scripts/vps-full-reset.sh
```

**Способ 2 — команды вручную:**

```bash
cd ~/AZbot

[ -f .env ] || cp .env.example .env

docker compose down
VOL=$(docker volume ls -q | grep postgres_data | head -1)
[ -n "$VOL" ] && docker volume rm "$VOL"

docker compose up -d
sleep 20
docker compose exec -T api python -c "from api.database import init_db; import asyncio; asyncio.run(init_db()); print('OK')"
curl -s http://localhost:8000/ready
docker compose restart bot api
```

**Важно:** пароль БД задаётся в `docker-compose.yml` (значение `postgres`). Не меняйте его только в одном месте — при смене пароля нужно править все три вхождения (db, bot, api) и заново пересоздать том.

---

**Если не хотите терять данные БД:**

Пароль задаётся в docker-compose; при перезапуске он не меняется. Если ошибка появилась после обновления репозитория — проверьте, что в `docker-compose.yml` у db, bot и api везде один и тот же `POSTGRES_PASSWORD`. Если том создавался старым compose с переменной из .env — либо приведите compose к текущему виду (пароль `postgres` в трёх местах), либо сделайте дамп и полный сброс.

**Диагностика на VPS:**

```bash
cd ~/AZbot
echo "В контейнере db: $(docker compose exec -T db env | grep POSTGRES_PASSWORD | sed 's/=.*/=***/')"
echo "В контейнере bot: $(docker compose exec -T bot env | grep POSTGRES_PASSWORD | sed 's/=.*/=***/')"
docker compose exec -T db psql -U postgres -d supply -c 'SELECT 1' 2>&1 && echo "Подключение к БД из контейнера db: OK"
curl -s http://localhost:8000/ready
```

Убедитесь, что `docker compose` запускается из каталога проекта (где лежит обновлённый docker-compose.yml).

#### Доступ к БД пропал через час (бот и дашборд не подключаются)

**Причина:** чаще всего том БД был создан с одним паролем, а в контейнеры bot/api при перезапуске попадал другой (или пустой). В текущей конфигурации пароль задан в `docker-compose.yml` одним значением `postgres` для db, bot и api — не зависит от .env.

**Что сделать на сервере (все команды — из каталога проекта):**

```bash
cd ~/AZbot
# Убедитесь, что в docker-compose.yml у db, bot, api везде POSTGRES_PASSWORD=postgres (без ${...})

docker compose build bot api --no-cache
docker compose up -d db
sleep 10
docker compose up -d bot api

# Проверка
sleep 5
curl -s http://localhost:8000/ready
docker compose logs bot --tail 15
```

Если доступ не восстановился — выполнить полный сброс БД (скрипт ниже); данные в БД будут удалены.

```bash
cd ~/AZbot
bash scripts/vps-full-reset.sh
```

**Чтобы проблема не повторялась:** все команды `docker compose` (в т.ч. из cron или systemd) всегда запускайте из каталога проекта. Пример systemd unit:

```ini
[Service]
WorkingDirectory=/opt/AZbot
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
```

---

**Дашборд показывает «Ошибка загрузки данных»:** чаще всего это 503/500 из-за отсутствия доступа API к БД. Проверьте:

1. Ответ API: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ready` — должно быть `200`. Если `503`, смотрите тело: `curl -s http://localhost:8000/ready`.
2. Логи API при старте: `docker compose logs api | head -30` — должна быть строка `Database connection OK`. Если есть `Database connection failed`, исправьте пароль/том по п. 4.1 выше.
3. После смены пароля или тома: `docker compose up -d api` и снова проверьте `/ready`.

### 4.2 Клавиатуры (импорты)

Если в логах бота есть ошибка про `supplier_management_keyboard`:

- Проверьте `bot/handlers/admin.py`: импортируйте только то, что реально есть в `bot/keyboards/__init__.py` (`order_keyboard`, `order_status_keyboard`, `admin_keyboard`).
- Либо добавьте в `bot/keyboards/__init__.py` экспорт `supplier_management_keyboard`, если такая клавиатура есть в `bot/keyboards/admin.py`.

### 4.3 Dashboard: package-lock.json

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

### 4.4 Dashboard: не хватает памяти при сборке (OOM)

Если при `docker compose build dashboard` процесс падает с «system ran out of memory» или «exited too early»:

1. **Добавьте swap на VPS** (2 GB), затем снова запустите сборку:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   docker compose build dashboard --no-cache
   ```
2. **Либо не собирайте Dashboard на VPS:** закомментируйте сервисы `dashboard` и `nginx` в `docker-compose.yml` и поднимайте только `db`, `redis`, `api`, `bot`. Dashboard можно собрать на своей машине (где больше RAM) и раздавать статику через свой веб-сервер или позже перенести готовый `build/` на сервер.

### 4.5 Версия docker-compose

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

### 5.3 Полная переустановка (чистый деплой или после смены схемы БД)

Если на сервере нет важных данных или вы обновляете код (в т.ч. модели БД), выполните полную пересборку и подъём:

```bash
cd /opt/AZbot   # или ваш путь
git pull

# Остановить и при необходимости удалить тома (данные БД будут потеряны)
docker compose down
# Опционально: docker volume rm azbot_postgres_data 2>/dev/null || true

# Собрать все образы без кэша (важно: бот и API должны подхватить актуальный db/models.py)
docker compose build --no-cache

# Запустить все сервисы
docker compose up -d

# Дождаться готовности БД и Redis (5–10 сек), затем инициализировать таблицы
sleep 5
docker compose exec api python -c "from api.database import init_db; import asyncio; asyncio.run(init_db()); print('OK')"

# Проверка API
curl -s http://localhost:8000/ready
# Ожидается: {"status":"ready","database":"ok"} или аналогично

curl -s http://localhost:8000/suppliers/
# Ожидается: [] или массив поставщиков
```

**Важно:** после изменений в `db/models.py` (типы полей, новые таблицы) обязательно выполнять `docker compose build --no-cache` для образов `api` и `bot`, иначе контейнеры могут использовать старую схему (например, `orders.id` как INTEGER вместо VARCHAR).

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
- [ ] `.env` создан из `.env.example`, заданы `BOT_TOKEN`, `ADMINS`, `SECRET_KEY` (пароль БД — в docker-compose)
- [ ] Исправлены импорты клавиатур в боте (при необходимости)
- [ ] В `dashboard` есть `package-lock.json`, образ dashboard собирается
- [ ] `docker compose up -d` выполнен, все нужные контейнеры Up
- [ ] База данных инициализирована (таблицы созданы)
- [ ] Бот запускается без ошибок импорта, отвечает в Telegram
- [ ] API отвечает на `/health`
- [ ] (Опционально) Dashboard собран и доступен
- [ ] (Опционально) Nginx настроен, SSL включён, `REACT_APP_API_URL` указывает на продакшен API

После выполнения этих шагов бот и остальные сервисы готовы к работе на VPS в продакшене.
