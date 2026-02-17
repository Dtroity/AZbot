from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from db.models import Supplier, ActivityLog


class SupplierService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_supplier(self, telegram_id: int, name: str, role: str = "supplier") -> Supplier:
        """Create new supplier"""
        supplier = Supplier(
            telegram_id=telegram_id,
            name=name,
            role=role,
            active=True
        )
        
        self.session.add(supplier)
        await self.session.commit()
        
        await self._log_activity(telegram_id, "supplier_created", f"Supplier {name} created")
        return supplier

    async def get_supplier_by_telegram(self, telegram_id: int) -> Optional[Supplier]:
        """Get supplier by telegram ID"""
        result = await self.session.execute(
            select(Supplier).where(Supplier.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_supplier_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Get supplier by ID"""
        result = await self.session.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()

    async def get_all_suppliers(self, active_only: bool = True) -> List[Supplier]:
        """Get all suppliers"""
        query = select(Supplier)
        if active_only:
            query = query.where(Supplier.active == True)
        
        result = await self.session.execute(query.order_by(Supplier.name))
        return result.scalars().all()

    async def activate_supplier(self, supplier_id: int) -> bool:
        """Activate supplier"""
        result = await self.session.execute(
            update(Supplier)
            .where(Supplier.id == supplier_id)
            .values(active=True)
        )
        
        if result.rowcount > 0:
            await self._log_activity(supplier_id, "supplier_activated", f"Supplier {supplier_id} activated")
            await self.session.commit()
            return True
        return False

    async def deactivate_supplier(self, supplier_id: int) -> bool:
        """Deactivate supplier"""
        result = await self.session.execute(
            update(Supplier)
            .where(Supplier.id == supplier_id)
            .values(active=False)
        )
        
        if result.rowcount > 0:
            await self._log_activity(supplier_id, "supplier_deactivated", f"Supplier {supplier_id} deactivated")
            await self.session.commit()
            return True
        return False

    async def update_supplier_name(self, supplier_id: int, name: str) -> bool:
        """Update supplier name"""
        result = await self.session.execute(
            update(Supplier)
            .where(Supplier.id == supplier_id)
            .values(name=name)
        )
        
        if result.rowcount > 0:
            await self._log_activity(supplier_id, "supplier_updated", f"Supplier {supplier_id} updated")
            await self.session.commit()
            return True
        return False

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin"""
        result = await self.session.execute(
            select(Supplier).where(
                and_(
                    Supplier.telegram_id == telegram_id,
                    Supplier.role == "admin"
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def register_user_if_new(self, telegram_id: int, name: str) -> Supplier:
        """Register user if not exists"""
        supplier = await self.get_supplier_by_telegram(telegram_id)
        if not supplier:
            supplier = await self.create_supplier(telegram_id, name)
        return supplier

    async def _log_activity(self, user_id: int, action: str, details: str = None):
        """Log user activity"""
        from db.models import ActivityLog
        
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details
        )
        self.session.add(log)
