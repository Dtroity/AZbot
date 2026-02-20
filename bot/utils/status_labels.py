# Русские подписи для статусов заказов (в БД хранятся на английском)

ORDER_STATUS_RU = {
    "NEW": "Новый",
    "ASSIGNED": "Назначен",
    "ACCEPTED": "Принят",
    "DECLINED": "Отклонён",
    "COMPLETED": "Завершён",
    "CANCELLED": "Отменён",
}


def order_status_ru(status: str) -> str:
    """Вернуть русское название статуса заказа."""
    return ORDER_STATUS_RU.get(status, status)
