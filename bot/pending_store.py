# Хранилище «ожидающего сообщения по заказу»: user_id -> order_id
# Используется, когда поставщик/админ нажал «Сообщение» или «Связаться с покупателем»
# и должен отправить текст. Не зависит от FSM, чтобы надёжно обрабатывать следующий ввод.

import time
from typing import Optional

_pending: dict[int, tuple[str, float]] = {}  # telegram_id -> (order_id, expires_at)
_redis = None
_backend: str = "memory"  # "memory" | "redis"
TTL = 600  # 10 минут


def set_redis(redis_client):
    """Подключить Redis (вызывается из main при наличии Redis)."""
    global _redis, _backend
    _redis = redis_client
    _backend = "redis" if redis_client else "memory"


async def set_pending(telegram_id: int, order_id: str) -> None:
    if _backend == "redis" and _redis:
        key = f"pending_order:{telegram_id}"
        await _redis.set(key, order_id, ex=TTL)
    else:
        _pending[telegram_id] = (order_id, time.time() + TTL)


async def get_pending(telegram_id: int) -> Optional[str]:
    if _backend == "redis" and _redis:
        key = f"pending_order:{telegram_id}"
        val = await _redis.get(key)
        return val if val else None
    if telegram_id in _pending:
        order_id, expires = _pending[telegram_id]
        if time.time() < expires:
            return order_id
        del _pending[telegram_id]
    return None


async def clear_pending(telegram_id: int) -> None:
    if _backend == "redis" and _redis:
        await _redis.delete(f"pending_order:{telegram_id}")
    elif telegram_id in _pending:
        del _pending[telegram_id]
