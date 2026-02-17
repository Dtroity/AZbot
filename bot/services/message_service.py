from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import OrderMessage, Order


class MessageService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_message(self, order_id: str, sender_id: int, message_text: str, message_type: str = "text") -> OrderMessage:
        """Send message to order"""
        message = OrderMessage(
            order_id=order_id,
            sender_id=sender_id,
            message_text=message_text,
            message_type=message_type
        )
        
        self.session.add(message)
        await self.session.commit()
        return message

    async def get_order_messages(self, order_id: str) -> List[OrderMessage]:
        """Get all messages for order"""
        result = await self.session.execute(
            select(OrderMessage)
            .where(OrderMessage.order_id == order_id)
            .order_by(OrderMessage.created_at)
        )
        return result.scalars().all()

    async def get_message_by_id(self, message_id: int) -> Optional[OrderMessage]:
        """Get message by ID"""
        result = await self.session.execute(
            select(OrderMessage).where(OrderMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def format_messages_for_display(self, order_id: str) -> str:
        """Format messages for display in telegram"""
        messages = await self.get_order_messages(order_id)
        if not messages:
            return "Нет сообщений"
        
        formatted = []
        for msg in messages:
            if msg.message_type == "system":
                formatted.append(f"🔧 {msg.message_text}")
            elif msg.message_type == "status_change":
                formatted.append(f"📊 {msg.message_text}")
            else:
                formatted.append(f"💬 {msg.message_text}")
        
        return "\n".join(formatted)

    async def add_system_message(self, order_id: str, text: str) -> OrderMessage:
        """Add system message"""
        return await self.send_message(order_id, 0, text, "system")

    async def add_status_message(self, order_id: str, status: str) -> OrderMessage:
        """Add status change message"""
        status_messages = {
            "NEW": "🆕 Заказ создан",
            "ASSIGNED": "👤 Назначен поставщик",
            "ACCEPTED": "✅ Заказ принят",
            "DECLINED": "❌ Заказ отклонен",
            "COMPLETED": "✅ Заказ завершен",
            "CANCELLED": "❌ Заказ отменен"
        }
        
        message_text = status_messages.get(status, f"📊 Статус изменен на {status}")
        return await self.send_message(order_id, 0, message_text, "status_change")
