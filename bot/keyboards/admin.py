from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# Тексты кнопок нижней панели (для обработчиков и единообразия)
BTN_ORDER = "📦 Создать заказ"
BTN_SUPPLIERS = "👥 Поставщики"
BTN_STATS = "📊 Статистика"
BTN_SEARCH = "🔍 Поиск заказов"
BTN_ADD_SUPPLIER = "➕ Добавить поставщика"
BTN_MENU = "◀️ Главное меню"

# Кнопки панели поставщика
BTN_MY_ORDERS = "📦 Мои заказы"
BTN_SUPPLIER_HELP = "📖 Справка"
BTN_CONTACT_BUYER = "📞 Связаться с покупателем"
BTN_SUPPLIER_MENU = "◀️ Меню"


def supplier_reply_keyboard() -> ReplyKeyboardMarkup:
    """Закреплённая панель для поставщика (ReplyKeyboard)."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=BTN_MY_ORDERS))
    builder.add(KeyboardButton(text=BTN_CONTACT_BUYER))
    builder.add(KeyboardButton(text=BTN_SUPPLIER_HELP))
    builder.add(KeyboardButton(text=BTN_SUPPLIER_MENU))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def admin_reply_keyboard() -> ReplyKeyboardMarkup:
    """Закреплённая внизу панель управления для админа (ReplyKeyboard)."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=BTN_ORDER))
    builder.add(KeyboardButton(text=BTN_SUPPLIERS))
    builder.add(KeyboardButton(text=BTN_STATS))
    builder.add(KeyboardButton(text=BTN_SEARCH))
    builder.add(KeyboardButton(text=BTN_ADD_SUPPLIER))
    builder.add(KeyboardButton(text=BTN_MENU))
    builder.adjust(2, 2, 2)  # по 2 кнопки в ряд
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def admin_keyboard() -> InlineKeyboardMarkup:
    """Inline-меню под сообщением (дублирует панель для удобства)."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📦 Создать заказ", callback_data="create_order"),
        InlineKeyboardButton(text="👥 Поставщики", callback_data="suppliers"),
    )
    builder.add(
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        InlineKeyboardButton(text="🔍 Поиск заказов", callback_data="search_orders"),
    )
    builder.adjust(2)
    return builder.as_markup()


def supplier_management_keyboard(supplier_id: int) -> InlineKeyboardMarkup:
    """Supplier management keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="✅ Активировать",
            callback_data=f"activate_supplier:{supplier_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="❌ Деактивировать",
            callback_data=f"deactivate_supplier:{supplier_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🔧 Фильтры",
            callback_data=f"filters:{supplier_id}"
        )
    )
    
    builder.adjust(1)
    
    return builder.as_markup()


def stats_keyboard() -> InlineKeyboardMarkup:
    """Statistics menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📈 Сегодня",
            callback_data="stats_today"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📅 Неделя",
            callback_data="stats_week"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📊 Месяц",
            callback_data="stats_month"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📋 Все время",
            callback_data="stats_all"
        )
    )
    
    builder.adjust(2)
    
    return builder.as_markup()
