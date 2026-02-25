# Диагностика распределения заказов по фильтрам

Команды выполняйте на сервере в каталоге проекта (где лежит `docker-compose.yml`).

## 1. Подключение к БД

```bash
docker exec -it supply_db psql -U postgres -d supply
```

Выйти из `psql`: `\q`

---

## 2. Поставщики и роли

Кто считается поставщиком (role=supplier) и кто администратором (role=admin):

```sql
SELECT id, name, telegram_id, active, role
FROM suppliers
ORDER BY id;
```

Убедитесь, что в распределении заказов участвуют только строки с `role = 'supplier'`. Пользователи с `role = 'admin'` в панели — заказчики/администраторы, им не должны отправляться заказы как поставщикам.

---

## 3. Фильтры по поставщикам

Проверка, что у каждого поставщика есть активные фильтры и ключевые слова:

```sql
SELECT s.id AS supplier_id, s.name AS supplier_name, s.role, s.active AS supplier_active,
       f.id AS filter_id, f.keyword, f.active AS filter_active, f.priority
FROM suppliers s
LEFT JOIN filters f ON f.supplier_id = s.id
WHERE s.role = 'supplier'
ORDER BY s.id, f.priority DESC, f.id;
```

Если у поставщика нет строк с `filter_id` или все фильтры `filter_active = false`, то по логике бота все неподходящие под других строки попадают первому активному поставщику (fallback). Результат: один поставщик получает весь список.

---

## 4. Последние заказы и кому назначены

Краткий обзор последних заказов и распределения:

```sql
SELECT o.id AS order_id, LEFT(o.text, 60) AS text_preview, o.supplier_id, s.name AS supplier_name, o.status, o.created_at
FROM orders o
LEFT JOIN suppliers s ON s.id = o.supplier_id
ORDER BY o.created_at DESC
LIMIT 30;
```

По одному заказу на поставщика и разный состав текста — распределение по фильтрам работает. Если одному и тому же поставщику приходят заказы с полным списком позиций — возможна ошибка логики или отсутствие/отключение фильтров у других поставщиков.

---

## 5. Один заказ — несколько поставщиков (по одному заказу на каждого)

Проверка, не дублируется ли один и тот же текст заказа разным поставщикам в один момент времени (по `created_at` и похожему `text`):

```sql
SELECT o.created_at::date AS day, COUNT(*) AS orders_count, COUNT(DISTINCT o.supplier_id) AS suppliers_count
FROM orders o
WHERE o.created_at > NOW() - INTERVAL '7 days'
GROUP BY o.created_at::date
ORDER BY day DESC;
```

Дополнительно: заказы с одинаковой датой и временем и одинаковой длиной текста:

```sql
SELECT o.id, o.supplier_id, s.name, LENGTH(o.text) AS len, o.created_at
FROM orders o
JOIN suppliers s ON s.id = o.supplier_id
WHERE o.created_at > NOW() - INTERVAL '3 days'
ORDER BY o.created_at DESC, o.id
LIMIT 50;
```

---

## 6. Версия кода бота на сервере

Убедиться, что на сервере запущена актуальная версия (распределение по строкам и по фильтрам):

```bash
docker compose exec bot cat /app/bot/services/order_service.py | head -80
```

Или посмотреть дату образа:

```bash
docker compose images bot
docker compose exec bot ls -la /app/bot/services/order_service.py
```

После изменений в коде пересобрать и перезапустить:

```bash
docker compose build bot --no-cache
docker compose up -d bot
```

---

## 7. Логи бота при создании заказа

При следующем создании заказа админом посмотреть логи:

```bash
docker compose logs -f bot
```

Искать ошибки и сообщения, связанные с заказами и API.

---

## Краткий чеклист

| Проверка | Команда / действие |
|----------|--------------------|
| Роли (supplier/admin) | SQL из пункта 2 |
| Наличие активных фильтров у поставщиков | SQL из пункта 3 |
| Кому какие заказы ушли | SQL из пункта 4 |
| Актуальность кода на сервере | Пункт 6, при необходимости пересборка и рестарт бота |

Если у всех поставщиков нет активных фильтров или только один активный поставщик с `role=supplier`, то весь список будет уходить одному поставщику. Если нужно, чтобы разным поставщикам уходили разные позиции, у каждого должен быть свой набор активных фильтров (ключевых слов).
