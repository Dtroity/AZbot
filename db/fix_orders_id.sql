-- Исправление типа колонки orders.id на VARCHAR(8), если она была создана как INTEGER.
-- Выполнить один раз при ошибке: 'str' object cannot be interpreted as an integer

-- Вариант 1: если в таблице нет данных или данные можно удалить
-- DROP TABLE IF EXISTS order_messages;
-- DROP TABLE IF EXISTS orders;
-- затем заново: docker compose exec api python -c "from api.database import init_db; import asyncio; asyncio.run(init_db()); print('OK')"

-- Вариант 2: изменить тип колонки (только если в orders нет строк или id можно привести к строке)
ALTER TABLE order_messages DROP CONSTRAINT IF EXISTS order_messages_order_id_fkey;
ALTER TABLE orders ALTER COLUMN id TYPE VARCHAR(8) USING id::TEXT;
ALTER TABLE order_messages ALTER COLUMN order_id TYPE VARCHAR(8) USING order_id::TEXT;
ALTER TABLE order_messages ADD CONSTRAINT order_messages_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders(id);
