from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.filters import Command

from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg

import re
from ..database import get_session
from ..services import OrderService, SupplierService, FilterService, MessageService
from ..keyboards import (
    admin_keyboard,
    admin_reply_keyboard,
    supplier_management_keyboard,
    stats_keyboard,
    BTN_ORDER,
    BTN_SUPPLIERS,
    BTN_STATS,
    BTN_SEARCH,
    BTN_ADD_SUPPLIER,
    BTN_MENU,
)
from ..config import settings
from ..utils import order_status_ru


class CreateOrderState(StatesGroup):
    waiting_for_text = State()


class ManageSupplierState(StatesGroup):
    waiting_for_name = State()
    waiting_for_filters = State()


admin_router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@admin_router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    """Handle /start command"""
    if _is_admin(message.from_user.id):
        await message.answer(
            "👋 <b>Админ-панель</b>\n\n"
            "Используйте кнопки ниже для управления заказами и поставщиками.",
            reply_markup=admin_reply_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer(
            "👋 Добро пожаловать в систему управления поставками!\n\n"
            "Вы будете получать заказы, соответствующие вашим фильтрам."
        )


@admin_router.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext):
    """Start order creation process"""
    await callback.message.answer(
        "📝 Введите список позиций заказа (каждая позиция — с новой строки). "
        "Система разнесёт позиции по поставщикам по фильтрам и отправит каждому поставщику один заказ с его позициями."
    )
    await state.set_state(CreateOrderState.waiting_for_text)
    await callback.answer()


@admin_router.message(CreateOrderState.waiting_for_text)
async def create_order_process(message: Message, state: FSMContext, bot: Bot):
    """Process order creation: one message = list of lines, grouped by supplier filters → one order per supplier."""
    if message.text == BTN_MENU:
        await state.clear()
        await message.answer(
            "◀️ Главное меню",
            reply_markup=admin_reply_keyboard(),
        )
        return
    if message.text and message.text.strip() == BTN_ORDER:
        await message.answer(
            "📝 Введите список позиций (каждая с новой строки). Позиции будут разнесены по поставщикам по фильтрам."
        )
        return
    async with get_session() as session:
        order_service = OrderService(session)
        created_orders = await order_service.create_orders_from_bulk_message(
            (message.text or "").strip(), message.from_user.id
        )
        if not created_orders:
            await message.answer("📝 Введите текст заказа (одна или несколько строк):")
            return
        for order in created_orders:
            if order.supplier_id:
                supplier_service = SupplierService(session)
                supplier = await supplier_service.get_supplier_by_id(order.supplier_id)
                if supplier:
                    from ..keyboards import order_keyboard
                    from aiogram.exceptions import TelegramBadRequest
                    try:
                        await bot.send_message(
                            supplier.telegram_id,
                            f"🆕 Новый заказ #{order.id}\n\n{order.text}",
                            reply_markup=order_keyboard(order.id),
                        )
                    except TelegramBadRequest as e:
                        if "chat not found" in str(e).lower() or "user not found" in str(e).lower():
                            pass
                        else:
                            raise
        await message.answer(
            f"✅ Создано заказов: {len(created_orders)}\n\n"
            + "\n".join([f"📦 #{order.id}" for order in created_orders])
        )
    await state.clear()


@admin_router.callback_query(F.data == "suppliers")
async def manage_suppliers(callback: CallbackQuery):
    """Show suppliers list"""
    async with get_session() as session:
        supplier_service = SupplierService(session)
        suppliers = await supplier_service.get_all_suppliers()
        
        if not suppliers:
            await callback.message.answer("📭 Поставщики не найдены")
            await callback.answer()
            return
        
        text = "👥 Список поставщиков:\n\n"
        for supplier in suppliers:
            status = "✅" if supplier.active else "❌"
            text += f"{status} {supplier.name} (ID: {supplier.id})\n"
        
        text += "\n\nИспользуйте /add_supplier для добавления нового поставщика"
        
        await callback.message.answer(text, reply_markup=admin_keyboard())
        await callback.answer()


@admin_router.message(Command("add_supplier"))
async def add_supplier_start(message: Message, state: FSMContext):
    """Start adding supplier"""
    await message.answer("📝 Введите имя поставщика:")
    await state.set_state(ManageSupplierState.waiting_for_name)


@admin_router.message(ManageSupplierState.waiting_for_name)
async def add_supplier_name(message: Message, state: FSMContext):
    """Get supplier name"""
    if message.text == BTN_MENU:
        await state.clear()
        await message.answer("◀️ Главное меню", reply_markup=admin_reply_keyboard())
        return
    await state.update_data(name=message.text)
    await message.answer(
        "📝 Теперь введите ключевые слова для фильтров (через запятую):\n"
        "Например: ноутбук, компьютер, техника"
    )
    await state.set_state(ManageSupplierState.waiting_for_filters)


@admin_router.message(ManageSupplierState.waiting_for_filters)
async def add_supplier_complete(message: Message, state: FSMContext):
    """Complete supplier creation"""
    if message.text == BTN_MENU:
        await state.clear()
        await message.answer("◀️ Главное меню", reply_markup=admin_reply_keyboard())
        return
    data = await state.get_data()
    name = data["name"]
    
    keywords = [kw.strip() for kw in message.text.split(",") if kw.strip()]
    try:
        async with get_session() as session:
            supplier_service = SupplierService(session)
            filter_service = FilterService(session)
            supplier = await supplier_service.create_supplier(0, name, "supplier")
            if keywords:
                await filter_service.bulk_create_filters(supplier.id, keywords)
            await message.answer(
                f"✅ Поставщик '{name}' создан!\n\n"
                f"ID: {supplier.id}\n"
                f"Фильтры: {', '.join(keywords) if keywords else 'нет'}\n\n"
                f"Поставщик сможет зарегистрироваться в боте командой /start"
            )
    except (asyncpg.exceptions.InvalidPasswordError, OSError, Exception):
        await message.answer(
            "Ошибка подключения к базе данных. Проверьте POSTGRES_PASSWORD в .env и перезапустите бота.",
            reply_markup=admin_reply_keyboard(),
        )
    await state.clear()


@admin_router.callback_query(F.data.startswith("activate_supplier:"))
async def activate_supplier(callback: CallbackQuery):
    """Activate supplier"""
    supplier_id = int(callback.data.split(":")[1])
    
    async with get_session() as session:
        supplier_service = SupplierService(session)
        success = await supplier_service.activate_supplier(supplier_id)
        
        if success:
            await callback.message.answer("✅ Поставщик активирован")
        else:
            await callback.message.answer("❌ Ошибка активации")
    
    await callback.answer()


@admin_router.callback_query(F.data.startswith("deactivate_supplier:"))
async def deactivate_supplier(callback: CallbackQuery):
    """Deactivate supplier"""
    supplier_id = int(callback.data.split(":")[1])
    
    async with get_session() as session:
        supplier_service = SupplierService(session)
        success = await supplier_service.deactivate_supplier(supplier_id)
        
        if success:
            await callback.message.answer("❌ Поставщик деактивирован")
        else:
            await callback.message.answer("❌ Ошибка деактивации")
    
    await callback.answer()


@admin_router.callback_query(F.data == "stats")
async def show_stats_menu(callback: CallbackQuery):
    """Show statistics menu"""
    await callback.message.answer(
        "📊 Выберите период статистики:",
        reply_markup=stats_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("stats_"))
async def show_stats(callback: CallbackQuery):
    """Show statistics for period"""
    try:
        period = callback.data.split("_")[1]
        async with get_session() as session:
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_admin(callback.from_user.id, limit=1000)
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            if period == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = now - timedelta(days=7)
            elif period == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = None
            if start_date:
                filtered_orders = [o for o in orders if o.created_at >= start_date]
            else:
                filtered_orders = orders
            total = len(filtered_orders)
            completed = len([o for o in filtered_orders if o.status == "COMPLETED"])
            pending = len([o for o in filtered_orders if o.status in ["NEW", "ASSIGNED", "ACCEPTED"]])
            cancelled = len([o for o in filtered_orders if o.status in ["DECLINED", "CANCELLED"]])
            period_label = {"today": "Сегодня", "week": "Неделя", "month": "Месяц", "all": "Всё время"}.get(period, period)
            text = f"📊 Статистика: {period_label}\n\n"
            text += f"📦 Всего заказов: {total}\n"
            text += f"✅ Выполнено: {completed}\n"
            text += f"⏳ В работе: {pending}\n"
            text += f"❌ Отменено: {cancelled}\n"
            if total > 0:
                completion_rate = (completed / total) * 100
                text += f"\n📈 Процент выполнения: {completion_rate:.1f}%"
            await callback.message.answer(text, reply_markup=admin_keyboard())
    except (asyncpg.exceptions.InvalidPasswordError, OSError, Exception):
        await callback.message.answer(
            "Ошибка подключения к базе данных. Проверьте POSTGRES_PASSWORD в .env и перезапустите бота.",
            reply_markup=admin_reply_keyboard(),
        )
    await callback.answer()


@admin_router.callback_query(F.data == "search_orders")
async def search_orders_start(callback: CallbackQuery, state: FSMContext):
    """Start order search"""
    await callback.message.answer("🔍 Введите текст для поиска заказов:")
    await state.set_state("search_orders")
    await callback.answer()


@admin_router.message(F.state == "search_orders")
async def search_orders_process(message: Message, state: FSMContext):
    """Process order search"""
    if message.text == BTN_MENU:
        await state.clear()
        await message.answer("◀️ Главное меню", reply_markup=admin_reply_keyboard())
        return
    try:
        async with get_session() as session:
            order_service = OrderService(session)
            orders = await order_service.search_orders(message.text)
            if not orders:
                await message.answer(
                    "📭 Заказы не найдены",
                    reply_markup=admin_reply_keyboard(),
                )
            else:
                text = f"🔍 Найдено заказов: {len(orders)}\n\n"
                for order in orders[:20]:
                    supplier_name = order.supplier.name if order.supplier else "Не назначен"
                    text += f"📦 #{order.id} - {order_status_ru(order.status)}\n"
                    text += f"👤 {supplier_name}\n"
                    text += f"📝 {order.text[:50]}...\n\n"
                await message.answer(text, reply_markup=admin_reply_keyboard())
    except (asyncpg.exceptions.InvalidPasswordError, OSError, Exception):
        await message.answer(
            "Ошибка подключения к базе данных. Проверьте POSTGRES_PASSWORD в .env и перезапустите бота.",
            reply_markup=admin_reply_keyboard(),
        )
    await state.clear()


# --- Обработчики кнопок закреплённой панели (только для админов) ---


@admin_router.message(F.text == BTN_MENU)
async def btn_menu(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "👋 <b>Главное меню</b>\n\nИспользуйте кнопки ниже.",
        reply_markup=admin_reply_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@admin_router.message(F.text == BTN_ORDER)
async def btn_create_order(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "📝 Введите список позиций заказа (каждая с новой строки). "
        "Позиции будут разнесены по поставщикам по фильтрам, каждому поставщику — один заказ."
    )
    await state.set_state(CreateOrderState.waiting_for_text)


@admin_router.message(F.text == BTN_SUPPLIERS)
async def btn_suppliers(message: Message):
    if not _is_admin(message.from_user.id):
        return
    try:
        async with get_session() as session:
            supplier_service = SupplierService(session)
            suppliers = await supplier_service.get_all_suppliers()
            if not suppliers:
                await message.answer(
                    "📭 Поставщики не найдены",
                    reply_markup=admin_reply_keyboard(),
                )
                return
            text = "👥 <b>Список поставщиков</b>\n\n"
            for s in suppliers:
                status = "✅" if s.active else "❌"
                text += f"{status} {s.name} (ID: {s.id})\n"
            text += "\nИспользуйте кнопку «➕ Добавить поставщика» или /add_supplier"
            await message.answer(
                text,
                reply_markup=admin_reply_keyboard(),
                parse_mode=ParseMode.HTML,
            )
    except (asyncpg.exceptions.InvalidPasswordError, OSError, Exception) as e:
        await message.answer(
            "Ошибка подключения к базе данных. Проверьте настройки (POSTGRES_PASSWORD в .env) и перезапустите бота.",
            reply_markup=admin_reply_keyboard(),
        )


@admin_router.message(F.text == BTN_STATS)
async def btn_stats(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "📊 Выберите период статистики:",
        reply_markup=stats_keyboard(),
    )


@admin_router.message(F.text == BTN_SEARCH)
async def btn_search(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("🔍 Введите текст для поиска заказов:")
    await state.set_state("search_orders")


@admin_router.message(F.text == BTN_ADD_SUPPLIER)
async def btn_add_supplier(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("📝 Введите имя поставщика:")
    await state.set_state(ManageSupplierState.waiting_for_name)


def _is_reply_to_order_notification(message: Message) -> bool:
    """Сообщение админа является ответом на уведомление «Новое сообщение по заказу»."""
    if not message.reply_to_message or not message.reply_to_message.text:
        return False
    if "Новое сообщение по заказу" not in message.reply_to_message.text:
        return False
    if not message.text or not message.text.strip():
        return False
    return True


@admin_router.message(
    lambda m: m.from_user and _is_admin(m.from_user.id) and _is_reply_to_order_notification(m),
)
async def admin_reply_to_supplier_message(message: Message, bot: Bot):
    """Ответ админа на сообщение поставщика по заказу (ответ на уведомление бота)."""
    replied = message.reply_to_message.text
    order_match = re.search(r"#([A-Za-z0-9]+)", replied)
    if not order_match:
        return
    order_id = order_match.group(1)
    try:
        async with get_session() as session:
            order_service = OrderService(session)
            message_service = MessageService(session)
            supplier_service = SupplierService(session)
            order = await order_service.get_order(order_id)
            if not order or order.admin_id != message.from_user.id:
                await message.answer("❌ Заказ не найден или нет доступа.")
                return
            await message_service.send_message(order_id, message.from_user.id, message.text.strip())
            supplier_telegram_id = None
            if order.supplier_id:
                supplier = await supplier_service.get_supplier_by_id(order.supplier_id)
                supplier_telegram_id = supplier.telegram_id if supplier else None
            if supplier_telegram_id:
                from aiogram.exceptions import TelegramBadRequest
                try:
                    await bot.send_message(
                        supplier_telegram_id,
                        f"💬 Ответ по заказу #{order_id}\n\n"
                        f"От: Администратор\n"
                        f"Сообщение: {message.text.strip()}",
                    )
                except TelegramBadRequest as e:
                    if "chat not found" not in str(e).lower() and "user not found" not in str(e).lower():
                        raise
            await message.reply("✅ Ответ отправлен поставщику.")
    except Exception as e:
        await message.reply("❌ Не удалось отправить ответ. Попробуйте позже.")


@admin_router.message(
    lambda m: m.from_user and _is_admin(m.from_user.id),
    ~F.state == "message_order",  # не перехватывать ввод сообщения для заказа
)
async def admin_fallback_menu(message: Message, state: FSMContext):
    """Если админ отправил любое сообщение и ни один обработчик не сработал — показать меню (не требовать /start)."""
    await state.clear()
    await message.answer(
        "👋 <b>Главное меню</b>\n\nИспользуйте кнопки ниже.",
        reply_markup=admin_reply_keyboard(),
        parse_mode=ParseMode.HTML,
    )
