from aiogram import Router, F
from aiogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import OrderService, MessageService


message_router = Router()


@message_router.message()
async def handle_text_message(message: Message):
    """Handle general text messages"""
    # Check if this is a reply to an order message
    if message.reply_to_message:
        await handle_order_reply(message)
    else:
        # Default response
        await message.answer(
            "🤔 Используйте кнопки для взаимодействия с заказами или команды:\n"
            "/start - Главное меню\n"
            "/my_orders - Мои заказы\n"
            "/profile - Мой профиль\n"
            "/help - Справка"
        )


async def handle_order_reply(message: Message):
    """Handle reply to order message"""
    async with get_session() as session:
        # Try to extract order ID from the replied message
        replied_text = message.reply_to_message.text or ""
        
        # Look for order ID pattern like "#ABC12345"
        import re
        order_match = re.search(r"#([A-Z0-9]{8})", replied_text)
        
        if not order_match:
            await message.answer("❌ Не удалось определить заказ. Используйте кнопку 'Сообщение' у заказа.")
            return
        
        order_id = order_match.group(1)
        
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        # Check if order exists and user has access
        order = await order_service.get_order(order_id)
        if not order:
            await message.answer("❌ Заказ не найден")
            return
        
        # supplier_id в Order — это ID из таблицы suppliers, не telegram_id; сравниваем с telegram
        from ..services import SupplierService
        supplier_service = SupplierService(session)
        supplier_telegram_id = None
        if order.supplier_id:
            supplier = await supplier_service.get_supplier_by_id(order.supplier_id)
            supplier_telegram_id = supplier.telegram_id if supplier else None
        
        is_admin = message.from_user.id == order.admin_id
        is_supplier = supplier_telegram_id is not None and message.from_user.id == supplier_telegram_id
        if not is_admin and not is_supplier:
            await message.answer("❌ У вас нет доступа к этому заказу")
            return
        
        # Add message
        await message_service.send_message(order_id, message.from_user.id, message.text)
        
        # Notify the other party
        bot = message.bot
        if is_admin and supplier_telegram_id:
            await bot.send_message(
                supplier_telegram_id,
                f"💬 Новое сообщение по заказу #{order_id}\n\n"
                f"От: Администратор\n"
                f"Сообщение: {message.text}"
            )
        elif is_supplier:
            await bot.send_message(
                order.admin_id,
                f"💬 Новое сообщение по заказу #{order_id}\n\n"
                f"От: {message.from_user.first_name}\n"
                f"Сообщение: {message.text}"
            )
        
        await message.reply("✅ Сообщение отправлено!")
