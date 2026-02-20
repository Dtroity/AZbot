from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import OrderService, SupplierService
from ..keyboards import order_keyboard, supplier_reply_keyboard, BTN_MY_ORDERS, BTN_SUPPLIER_HELP, BTN_CONTACT_BUYER, BTN_SUPPLIER_MENU
from ..utils import order_status_ru
from ..pending_store import set_pending
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
                "Вы активный поставщик. Используйте кнопки ниже.",
                reply_markup=supplier_reply_keyboard(),
            )
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_supplier(supplier.id, status="ACCEPTED")
            if orders:
                await message.answer("📦 Ваши активные заказы:")
                for order in orders:
                    await message.answer(
                        f"📦 #{order.id}\n{order.text}",
                        reply_markup=order_keyboard(order.id),
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
        orders = await order_service.get_orders_by_supplier(supplier.id)
        
        if not orders:
            await message.answer("📭 У вас нет заказов", reply_markup=supplier_reply_keyboard())
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
            text += f"{status_emoji} #{order.id} - {order_status_ru(order.status)}\n"
            text += f"📝 {order.text[:50]}...\n"
            text += f"📅 {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        await message.answer(text, reply_markup=supplier_reply_keyboard())


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
        all_orders = await order_service.get_orders_by_supplier(supplier.id)
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
            for filter_obj in filters[:10]:
                text += f"• {filter_obj.keyword}\n"
            if len(filters) > 10:
                text += f"... и еще {len(filters) - 10}\n"
        else:
            text += "Нет фильтров\n"
        await message.answer(text, reply_markup=supplier_reply_keyboard())


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
    await message.answer(text, reply_markup=supplier_reply_keyboard())


@supplier_router.message(F.text == BTN_MY_ORDERS)
async def btn_my_orders(message: Message):
    """Handle 'Мои заказы' button."""
    await my_orders(message)


@supplier_router.message(F.text == BTN_SUPPLIER_HELP)
async def btn_supplier_help(message: Message):
    """Handle 'Справка' button."""
    await supplier_help(message)


@supplier_router.message(F.text == BTN_CONTACT_BUYER)
async def contact_buyer_ask_order(message: Message, state: FSMContext):
    """Кнопка «Связаться с покупателем» — запрос ID заказа."""
    await state.set_state("contact_buyer_wait_order")
    await message.answer("Введите ID заказа (например DE5A2138) или /cancel для отмены:")


@supplier_router.message(StateFilter("contact_buyer_wait_order"), F.text)
async def contact_buyer_got_order(message: Message, state: FSMContext):
    """Обработка введённого ID заказа для связи с покупателем."""
    if not message.text or not message.text.strip():
        await message.answer("Введите ID заказа или /cancel.")
        return
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Отменено.", reply_markup=supplier_reply_keyboard())
        return
    order_id = message.text.strip().upper()
    async with get_session() as session:
        supplier_service = SupplierService(session)
        order_service = OrderService(session)
        supplier = await supplier_service.get_supplier_by_telegram(message.from_user.id)
        if not supplier:
            await state.clear()
            await message.answer("❌ Вы не зарегистрированы как поставщик.", reply_markup=supplier_reply_keyboard())
            return
        order = await order_service.get_order(order_id)
        if not order:
            await message.answer("Заказ с таким ID не найден. Введите ID заказа или /cancel.")
            return
        if order.supplier_id != supplier.id:
            await state.clear()
            await message.answer("Этот заказ не назначен вам.", reply_markup=supplier_reply_keyboard())
            return
    await state.clear()
    await set_pending(message.from_user.id, order.id)
    await message.answer("📞 Введите сообщение для покупателя (или /cancel для отмены):")


@supplier_router.message(F.text == BTN_SUPPLIER_MENU)
async def btn_supplier_menu(message: Message):
    """Handle 'Меню' button — show welcome and active orders."""
    async with get_session() as session:
        supplier_service = SupplierService(session)
        supplier = await supplier_service.get_supplier_by_telegram(message.from_user.id)
        if not supplier:
            await message.answer("❌ Вы не зарегистрированы как поставщик.")
            return
        if not supplier.active:
            await message.answer(
                f"👋 {supplier.name}, ваш аккаунт неактивен. Свяжитесь с администратором.",
                reply_markup=supplier_reply_keyboard(),
            )
            return
        await message.answer(
            f"👋 {supplier.name}, главное меню. Используйте кнопки ниже.",
            reply_markup=supplier_reply_keyboard(),
        )
        order_service = OrderService(session)
        orders = await order_service.get_orders_by_supplier(supplier.id, status="ACCEPTED")
        if orders:
            await message.answer("📦 Ваши активные заказы:")
            for order in orders:
                await message.answer(
                    f"📦 #{order.id}\n{order.text}",
                    reply_markup=order_keyboard(order.id),
                )
