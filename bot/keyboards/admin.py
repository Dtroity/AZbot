from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard() -> InlineKeyboardMarkup:
    """Main admin menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📦 Создать заказ",
            callback_data="create_order"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="👥 Поставщики",
            callback_data="suppliers"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="stats"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🔍 Поиск заказов",
            callback_data="search_orders"
        )
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
