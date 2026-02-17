from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import OrderService, SupplierService
from ..keyboards import order_keyboard
from ..config import settings


supplier_router = Router()


@supplier_router.message(Command("start"))
async def supplier_start(message: Message):
    """Handle supplier registration"""
    async with get_session() as session:
        supplier_service = SupplierService(session)
        
        # Register or get supplier
        supplier = await supplier_service.register_user_if_new(
            message.from_user.id,
            message.from_user.first_name
        )
        
        if supplier.role == "admin":
            from ..keyboards import admin_keyboard
            await message.answer(
                "👋 Добро пожаловать в админ-панель!",
                reply_markup=admin_keyboard()
            )
        elif supplier.active:
            await message.answer(
                f"👋 Добро пожаловать, {supplier.name}!\n\n"
                "Вы активный поставщик. Будьте готовы к поступлению заказов."
            )
            
            # Show active orders
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_supplier(
                message.from_user.id, 
                status="ACCEPTED"
            )
            
            if orders:
                await message.answer("📦 Ваши активные заказы:")
                for order in orders:
                    await message.answer(
                        f"📦 #{order.id}\n{order.text}",
                        reply_markup=order_keyboard(order.id)
                    )
        else:
            await message.answer(
                f"👋 Добро пожаловать, {supplier.name}!\n\n"
                "Ваш аккаунт неактивен. Свяжитесь с администратором."
            )


@supplier_router.message(Command("my_orders"))
async def my_orders(message: Message):
    """Show supplier's orders"""
    async with get_session() as session:
        order_service = OrderService(session)
        
        # Check if supplier exists and is active
        supplier_service = SupplierService(session)
        supplier = await supplier_service.get_supplier_by_telegram(message.from_user.id)
        
        if not supplier:
            await message.answer("❌ Вы не зарегистрированы как поставщик")
            return
        
        if not supplier.active:
            await message.answer("❌ Ваш аккаунт неактивен")
            return
        
        # Get orders
        orders = await order_service.get_orders_by_supplier(message.from_user.id)
        
        if not orders:
            await message.answer("📭 У вас нет заказов")
            return
        
        text = f"📦 Ваши заказы ({len(orders)}):\n\n"
        
        for order in orders:
            status_emoji = {
                "NEW": "🆕",
                "ASSIGNED": "👤",
                "ACCEPTED": "✅",
                "COMPLETED": "✅",
                "DECLINED": "❌",
                "CANCELLED": "❌"
            }.get(order.status, "📋")
            
            text += f"{status_emoji} #{order.id} - {order.status}\n"
            text += f"📝 {order.text[:50]}...\n"
            text += f"📅 {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await message.answer(text)


@supplier_router.message(Command("profile"))
async def supplier_profile(message: Message):
    """Show supplier profile"""
    async with get_session() as session:
        supplier_service = SupplierService(session)
        
        supplier = await supplier_service.get_supplier_by_telegram(message.from_user.id)
        if not supplier:
            await message.answer("❌ Вы не зарегистрированы как поставщик")
            return
        
        # Get filters
        from ..services import FilterService
        filter_service = FilterService(session)
        filters = await filter_service.get_filters_by_supplier(supplier.id)
        
        # Get order stats
        order_service = OrderService(session)
        all_orders = await order_service.get_orders_by_supplier(message.from_user.id)
        
        stats = {
            "total": len(all_orders),
            "completed": len([o for o in all_orders if o.status == "COMPLETED"]),
            "accepted": len([o for o in all_orders if o.status == "ACCEPTED"]),
            "declined": len([o for o in all_orders if o.status == "DECLINED"]),
        }
        
        text = f"👤 Профиль поставщика\n\n"
        text += f"📛 Имя: {supplier.name}\n"
        text += f"🆔 ID: {supplier.id}\n"
        text += f"✅ Статус: {'Активен' if supplier.active else 'Неактивен'}\n"
        text += f"📅 Регистрация: {supplier.created_at.strftime('%Y-%m-%d')}\n\n"
        
        text += f"📊 Статистика заказов:\n"
        text += f"📦 Всего: {stats['total']}\n"
        text += f"✅ Выполнено: {stats['completed']}\n"
        text += f"🔄 В работе: {stats['accepted']}\n"
        text += f"❌ Отклонено: {stats['declined']}\n\n"
        
        if stats['total'] > 0:
            completion_rate = (stats['completed'] / stats['total']) * 100
            text += f"📈 Процент выполнения: {completion_rate:.1f}%\n\n"
        
        text += f"🔍 Ваши фильтры ({len(filters)}):\n"
        if filters:
            for filter_obj in filters[:10]:  # Show first 10 filters
                text += f"• {filter_obj.keyword}\n"
            if len(filters) > 10:
                text += f"... и еще {len(filters) - 10}\n"
        else:
            text += "Нет фильтров\n"
        
        await message.answer(text)


@supplier_router.message(Command("help"))
async def supplier_help(message: Message):
    """Show help for suppliers"""
    text = """
📖 Справка поставщика

🔸 /start - Регистрация/главное меню
🔸 /my_orders - Мои заказы
🔸 /profile - Мой профиль
🔸 /help - Эта справка

📦 Работа с заказами:
• При получении заказа вы увидите кнопки действий
• ✅ Принять - начать работу над заказом
• ❌ Отклонить - отказаться от заказа
• 💬 Сообщение - отправить сообщение администратору
• ✅ Завершить - отметить заказ как выполненный

🔍 Фильтры:
• Заказы автоматически распределяются по ключевым словам
• Настройка фильтров доступна администратору

💬 Сообщения:
• Все сообщения по заказу видны администратору
• Используйте кнопку "Сообщение" для связи

❓ Если у вас есть вопросы, свяжитесь с администратором.
    """
    
    await message.answer(text)
