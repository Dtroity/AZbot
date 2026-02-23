import uuid
from datetime import datetime
from typing import List, Optional, Dict
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from db.models import Order, OrderMessage, Supplier, Filter, ActivityLog


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def generate_id(self) -> str:
        """Generate short order ID"""
        return str(uuid.uuid4())[:8].upper()

    async def create_order(
        self, text: str, admin_id: int, assign_supplier_id: Optional[int] = None
    ) -> Order:
        """Create new order. If assign_supplier_id is set, assign to that supplier; else find by filters."""
        order_id = self.generate_id()
        
        order = Order()
        order.id = order_id
        order.text = text
        order.status = "NEW"
        order.admin_id = admin_id
        
        self.session.add(order)
        await self.session.flush()
        
        if assign_supplier_id is not None:
            order.supplier_id = assign_supplier_id
            order.assigned_at = datetime.utcnow()
            order.status = "ASSIGNED"
        else:
            supplier = await self._find_suitable_supplier(text)
            if supplier:
                order.supplier_id = supplier.id
                order.assigned_at = datetime.utcnow()
                order.status = "ASSIGNED"
        
        await self._log_activity(admin_id, "order_created", f"Order {order_id} created")
        
        await self.session.commit()
        return order

    async def create_orders_from_bulk_message(self, message_text: str, admin_id: int) -> List[Order]:
        """
        Parse message as multiple lines; assign each line to a supplier by filters;
        group lines by supplier and create one order per supplier with their lines.
        """
        lines = [
            line.strip()
            for line in (message_text or "").strip().splitlines()
            if line.strip()
        ]
        if not lines:
            return []

        result = await self.session.execute(
            select(Supplier)
            .options(selectinload(Supplier.filters))
            .where(
                and_(
                    Supplier.active == True,
                    Supplier.role == "supplier"
                )
            )
            .order_by(Supplier.created_at)
        )
        suppliers = result.scalars().all()
        if not suppliers:
            return []

        # For each line, find the best matching supplier (by filters)
        by_supplier: Dict[int, List[str]] = defaultdict(list)
        for line in lines:
            supplier = await self._find_suitable_supplier(line)
            if supplier:
                by_supplier[supplier.id].append(line)

        created = []
        for supplier_id, line_list in by_supplier.items():
            order_text = "\n".join(line_list)
            order = await self.create_order(
                order_text, admin_id, assign_supplier_id=supplier_id
            )
            created.append(order)
        return created

    async def _find_suitable_supplier(self, order_text: str) -> Optional[Supplier]:
        """Find best supplier based on filters"""
        # Get all active suppliers with their filters
        result = await self.session.execute(
            select(Supplier)
            .options(selectinload(Supplier.filters))
            .where(
                and_(
                    Supplier.active == True,
                    Supplier.role == "supplier"
                )
            )
            .order_by(Supplier.created_at)
        )
        suppliers = result.scalars().all()
        
        if not suppliers:
            return None
        
        # Find suppliers with matching keywords
        order_lower = order_text.lower()
        matching_suppliers = []
        
        for supplier in suppliers:
            for filter_obj in supplier.filters:
                if filter_obj.active and filter_obj.keyword.lower() in order_lower:
                    matching_suppliers.append((supplier, filter_obj.priority))
                    break
        
        if not matching_suppliers:
            # If no matches, return first active supplier
            return suppliers[0]
        
        # Sort by priority and return best match
        matching_suppliers.sort(key=lambda x: x[1], reverse=True)
        return matching_suppliers[0][0]

    async def accept_order(self, order_id: str, supplier_id: int) -> bool:
        """Accept order by supplier"""
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                status="ACCEPTED",
                supplier_id=supplier_id,
                assigned_at=datetime.utcnow()
            )
        )
        
        if result.rowcount > 0:
            await self._log_activity(supplier_id, "order_accepted", f"Order {order_id} accepted")
            await self.session.commit()
            return True
        return False

    async def decline_order(self, order_id: str, supplier_id: int) -> bool:
        """Decline order and try to reassign"""
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                status="NEW",
                supplier_id=None,
                assigned_at=None
            )
        )
        
        if result.rowcount > 0:
            # Try to reassign to another supplier
            order = await self.get_order(order_id)
            if order:
                new_supplier = await self._find_suitable_supplier(order.text)
                if new_supplier and new_supplier.id != supplier_id:
                    order.supplier_id = new_supplier.id
                    order.assigned_at = datetime.utcnow()
                    order.status = "ASSIGNED"
            
            await self._log_activity(supplier_id, "order_declined", f"Order {order_id} declined")
            await self.session.commit()
            return True
        return False

    async def complete_order(self, order_id: str, supplier_id: int) -> bool:
        """Complete order"""
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                status="COMPLETED",
                completed_at=datetime.utcnow()
            )
        )
        
        if result.rowcount > 0:
            await self._log_activity(supplier_id, "order_completed", f"Order {order_id} completed")
            await self.session.commit()
            return True
        return False

    async def cancel_order(self, order_id: str, supplier_id: int) -> bool:
        """Cancel order"""
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                status="CANCELLED",
                supplier_id=None,
                assigned_at=None
            )
        )
        
        if result.rowcount > 0:
            await self._log_activity(supplier_id, "order_cancelled", f"Order {order_id} cancelled")
            await self.session.commit()
            return True
        return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.supplier))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_orders_by_supplier(self, supplier_id: int, status: Optional[str] = None) -> List[Order]:
        """Get orders for specific supplier"""
        query = select(Order).where(Order.supplier_id == supplier_id)
        if status:
            query = query.where(Order.status == status)
        
        result = await self.session.execute(query.order_by(Order.created_at.desc()))
        return result.scalars().all()

    async def get_orders_by_admin(self, admin_id: int, limit: int = 50) -> List[Order]:
        """Get orders created by admin"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.supplier))
            .where(Order.admin_id == admin_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def search_orders(self, query: str, limit: int = 20) -> List[Order]:
        """Search orders by text"""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.supplier))
            .where(Order.text.ilike(f"%{query}%"))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def add_message(self, order_id: str, sender_id: int, message_text: str, message_type: str = "text") -> OrderMessage:
        """Add message to order"""
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

    async def _log_activity(self, user_id: int, action: str, details: str = None):
        """Log user activity"""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details
        )
        self.session.add(log)
