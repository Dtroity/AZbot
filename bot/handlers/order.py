from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services import OrderService, MessageService
from ..keyboards import order_keyboard, order_status_keyboard


order_router = Router()


@order_router.callback_query(F.data.startswith("accept:"))
async def accept_order(callback: CallbackQuery, bot: Bot):
    """Accept order"""
    order_id = callback.data.split(":")[1]
    
    async with get_session() as session:
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        success = await order_service.accept_order(order_id, callback.from_user.id)
        
        if success:
            # Add status message
            await message_service.add_status_message(order_id, "ACCEPTED")
            
            # Update keyboard
            await callback.message.edit_reply_markup(
                reply_markup=order_status_keyboard(order_id, "ACCEPTED")
            )
            
            await callback.answer("✅ Заказ принят!")
        else:
            await callback.answer("❌ Ошибка принятия заказа", show_alert=True)


@order_router.callback_query(F.data.startswith("decline:"))
async def decline_order(callback: CallbackQuery, bot: Bot):
    """Decline order"""
    order_id = callback.data.split(":")[1]
    
    async with get_session() as session:
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        success = await order_service.decline_order(order_id, callback.from_user.id)
        
        if success:
            # Add status message
            await message_service.add_status_message(order_id, "DECLINED")
            
            # Check if order was reassigned
            order = await order_service.get_order(order_id)
            
            if order.supplier_id and order.supplier_id != callback.from_user.id:
                # Order was reassigned to another supplier
                supplier_service = SupplierService(session)
                new_supplier = await supplier_service.get_supplier_by_id(order.supplier_id)
                
                if new_supplier:
                    await bot.send_message(
                        new_supplier.telegram_id,
                        f"🆕 Новый заказ #{order.id}\n\n{order.text}",
                        reply_markup=order_keyboard(order_id)
                    )
                
                await callback.message.edit_text(
                    f"❌ Заказ отклонен и переназначен другому поставщику",
                    reply_markup=None
                )
                await callback.answer("❌ Заказ отклонен")
            else:
                # Order not reassigned
                await callback.message.edit_text(
                    f"❌ Заказ отклонен",
                    reply_markup=None
                )
                await callback.answer("❌ Заказ отклонен")
        else:
            await callback.answer("❌ Ошибка отклонения заказа", show_alert=True)


@order_router.callback_query(F.data.startswith("complete:"))
async def complete_order(callback: CallbackQuery):
    """Complete order"""
    order_id = callback.data.split(":")[1]
    
    async with get_session() as session:
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        success = await order_service.complete_order(order_id, callback.from_user.id)
        
        if success:
            # Add status message
            await message_service.add_status_message(order_id, "COMPLETED")
            
            await callback.message.edit_text(
                f"✅ Заказ #{order_id} завершен!",
                reply_markup=None
            )
            await callback.answer("✅ Заказ завершен!")
        else:
            await callback.answer("❌ Ошибка завершения заказа", show_alert=True)


@order_router.callback_query(F.data.startswith("cancel:"))
async def cancel_order(callback: CallbackQuery):
    """Cancel order"""
    order_id = callback.data.split(":")[1]
    
    async with get_session() as session:
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        success = await order_service.cancel_order(order_id, callback.from_user.id)
        
        if success:
            # Add status message
            await message_service.add_status_message(order_id, "CANCELLED")
            
            await callback.message.edit_text(
                f"❌ Заказ #{order_id} отменен",
                reply_markup=None
            )
            await callback.answer("❌ Заказ отменен")
        else:
            await callback.answer("❌ Ошибка отмены заказа", show_alert=True)


@order_router.callback_query(F.data.startswith("message:"))
async def message_order_start(callback: CallbackQuery, state: FSMContext):
    """Start messaging for order"""
    order_id = callback.data.split(":")[1]
    
    await state.update_data(order_id=order_id)
    await callback.message.answer(
        "💬 Введите сообщение для заказа:",
        reply_markup=None
    )
    await state.set_state("message_order")
    await callback.answer()


@order_router.message(F.state == "message_order")
async def message_order_process(message: Message, state: FSMContext, bot: Bot):
    """Process order message"""
    data = await state.get_data()
    order_id = data["order_id"]
    
    async with get_session() as session:
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        # Add message
        await message_service.send_message(order_id, message.from_user.id, message.text)
        
        # Get order details
        order = await order_service.get_order(order_id)
        
        # Notify admin
        if order.admin_id != message.from_user.id:
            await bot.send_message(
                order.admin_id,
                f"💬 Новое сообщение по заказу #{order_id}\n\n"
                f"От: {message.from_user.first_name}\n"
                f"Сообщение: {message.text}"
            )
        
        # Notify supplier if message from admin
        if order.supplier_id and order.supplier_id != message.from_user.id:
            supplier_service = SupplierService(session)
            supplier = await supplier_service.get_supplier_by_id(order.supplier_id)
            
            if supplier:
                await bot.send_message(
                    supplier.telegram_id,
                    f"💬 Новое сообщение по заказу #{order_id}\n\n"
                    f"От: Админ\n"
                    f"Сообщение: {message.text}"
                )
        
        await message.answer("✅ Сообщение отправлено!")
    
    await state.clear()


@order_router.callback_query(F.data.startswith("status:"))
async def show_order_status(callback: CallbackQuery):
    """Show order status and details"""
    order_id = callback.data.split(":")[1]
    
    async with get_session() as session:
        order_service = OrderService(session)
        message_service = MessageService(session)
        
        order = await order_service.get_order(order_id)
        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        
        supplier_name = order.supplier.name if order.supplier else "Не назначен"
        
        text = f"📦 Заказ #{order.id}\n\n"
        text += f"📝 {order.text}\n\n"
        text += f"📊 Статус: {order.status}\n"
        text += f"👤 Поставщик: {supplier_name}\n"
        text += f"📅 Создан: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        if order.assigned_at:
            text += f"👤 Назначен: {order.assigned_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        if order.completed_at:
            text += f"✅ Завершен: {order.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        # Show messages
        messages = await message_service.get_order_messages(order_id)
        if messages:
            text += f"\n💬 Сообщения ({len(messages)}):\n"
            for msg in messages[-5:]:  # Show last 5 messages
                if msg.message_type == "text":
                    text += f"• {msg.message_text}\n"
        
        await callback.message.answer(text)
        await callback.answer()


@order_router.callback_query(F.data.startswith("history:"))
async def show_order_history(callback: CallbackQuery):
    """Show full order message history"""
    order_id = callback.data.split(":")[1]
    
    async with get_session() as session:
        message_service = MessageService(session)
        
        messages = await message_service.get_order_messages(order_id)
        if not messages:
            await callback.answer("Нет сообщений", show_alert=True)
            return
        
        text = f"📦 История заказа #{order_id}\n\n"
        
        for msg in messages:
            if msg.message_type == "system":
                text += f"🔧 {msg.created_at.strftime('%H:%M')} - {msg.message_text}\n"
            elif msg.message_type == "status_change":
                text += f"📊 {msg.created_at.strftime('%H:%M')} - {msg.message_text}\n"
            else:
                text += f"💬 {msg.created_at.strftime('%H:%M')} - {msg.message_text}\n"
        
        # Split if too long
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await callback.message.answer(part)
        else:
            await callback.message.answer(text)
        
        await callback.answer()


@order_router.callback_query(F.data.startswith("reassign:"))
async def reassign_order_start(callback: CallbackQuery, state: FSMContext):
    """Start order reassignment"""
    order_id = callback.data.split(":")[1]
    
    await state.update_data(order_id=order_id)
    await callback.message.answer(
        "🔄 Переназначение заказа - введите ID нового поставщика:",
        reply_markup=None
    )
    await state.set_state("reassign_order")
    await callback.answer()


@order_router.message(F.state == "reassign_order")
async def reassign_order_process(message: Message, state: FSMContext, bot: Bot):
    """Process order reassignment"""
    data = await state.get_data()
    order_id = data["order_id"]
    
    try:
        new_supplier_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный ID поставщика. Введите число.")
        return
    
    async with get_session() as session:
        order_service = OrderService(session)
        supplier_service = SupplierService(session)
        message_service = MessageService(session)
        
        # Check if supplier exists
        supplier = await supplier_service.get_supplier_by_id(new_supplier_id)
        if not supplier:
            await message.answer("❌ Поставщик не найден")
            await state.clear()
            return
        
        # Reassign order
        from sqlalchemy import update
        from datetime import datetime
        
        result = await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                supplier_id=new_supplier_id,
                assigned_at=datetime.utcnow(),
                status="ASSIGNED"
            )
        )
        
        if result.rowcount > 0:
            # Add system message
            await message_service.add_system_message(
                order_id, 
                f"🔄 Заказ переназначен поставщику {supplier.name}"
            )
            
            # Notify new supplier
            order = await order_service.get_order(order_id)
            await bot.send_message(
                supplier.telegram_id,
                f"🆕 Новый заказ #{order.id}\n\n{order.text}",
                reply_markup=order_keyboard(order_id)
            )
            
            await message.answer(f"✅ Заказ #{order_id} переназначен поставщику {supplier.name}")
        else:
            await message.answer("❌ Ошибка переназначения заказа")
    
    await state.clear()
