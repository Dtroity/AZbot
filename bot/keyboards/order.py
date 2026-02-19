from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Main order action keyboard for suppliers"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="✅ Принять",
            callback_data=f"accept:{order_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"decline:{order_id}"
        )
    )
    
    builder.adjust(2)
    builder.add(
        InlineKeyboardButton(
            text="💬 Сообщение",
            callback_data=f"message:{order_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📞 Связаться с покупателем",
            callback_data=f"contact_buyer:{order_id}"
        )
    )
    return builder.as_markup()


def order_status_keyboard(order_id: str, status: str) -> InlineKeyboardMarkup:
    """Status management keyboard for assigned suppliers"""
    builder = InlineKeyboardBuilder()
    
    if status == "ACCEPTED":
        builder.add(
            InlineKeyboardButton(
                text="✅ Завершить",
                callback_data=f"complete:{order_id}"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"cancel:{order_id}"
            )
        )
    elif status == "NEW":
        builder.add(
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept:{order_id}"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"decline:{order_id}"
            )
        )
    
    builder.adjust(2)
    builder.add(
        InlineKeyboardButton(
            text="💬 Сообщение",
            callback_data=f"message:{order_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📞 Связаться с покупателем",
            callback_data=f"contact_buyer:{order_id}"
        )
    )
    return builder.as_markup()


def admin_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Admin order management keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📊 Статус",
            callback_data=f"status:{order_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="💬 История",
            callback_data=f"history:{order_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🔄 Переназначить",
            callback_data=f"reassign:{order_id}"
        )
    )
    
    builder.adjust(1)
    
    return builder.as_markup()
