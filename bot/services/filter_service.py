from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_

from db.models import Filter, ActivityLog


class FilterService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_filter(self, supplier_id: int, keyword: str, priority: int = 0) -> Filter:
        """Create new filter for supplier"""
        filter_obj = Filter(
            supplier_id=supplier_id,
            keyword=keyword,
            priority=priority,
            active=True
        )
        
        self.session.add(filter_obj)
        await self.session.commit()
        
        await self._log_activity(supplier_id, "filter_created", f"Filter '{keyword}' created")
        return filter_obj

    async def get_filters_by_supplier(self, supplier_id: int, active_only: bool = True) -> List[Filter]:
        """Get all filters for supplier"""
        query = select(Filter).where(Filter.supplier_id == supplier_id)
        if active_only:
            query = query.where(Filter.active == True)
        
        result = await self.session.execute(query.order_by(Filter.priority.desc(), Filter.keyword))
        return result.scalars().all()

    async def get_filter_by_id(self, filter_id: int) -> Optional[Filter]:
        """Get filter by ID"""
        result = await self.session.execute(
            select(Filter).where(Filter.id == filter_id)
        )
        return result.scalar_one_or_none()

    async def update_filter(self, filter_id: int, keyword: str = None, priority: int = None) -> bool:
        """Update filter"""
        filter_obj = await self.get_filter_by_id(filter_id)
        if not filter_obj:
            return False
        
        updates = {}
        if keyword is not None:
            updates["keyword"] = keyword
        if priority is not None:
            updates["priority"] = priority
        
        if updates:
            result = await self.session.execute(
                update(Filter)
                .where(Filter.id == filter_id)
                .values(**updates)
            )
            
            if result.rowcount > 0:
                await self._log_activity(filter_obj.supplier_id, "filter_updated", f"Filter {filter_id} updated")
                await self.session.commit()
                return True
        return False

    async def delete_filter(self, filter_id: int) -> bool:
        """Delete filter"""
        filter_obj = await self.get_filter_by_id(filter_id)
        if not filter_obj:
            return False
        
        result = await self.session.execute(
            delete(Filter).where(Filter.id == filter_id)
        )
        
        if result.rowcount > 0:
            await self._log_activity(filter_obj.supplier_id, "filter_deleted", f"Filter '{filter_obj.keyword}' deleted")
            await self.session.commit()
            return True
        return False

    async def activate_filter(self, filter_id: int) -> bool:
        """Activate filter"""
        result = await self.session.execute(
            update(Filter)
            .where(Filter.id == filter_id)
            .values(active=True)
        )
        
        if result.rowcount > 0:
            filter_obj = await self.get_filter_by_id(filter_id)
            await self._log_activity(filter_obj.supplier_id, "filter_activated", f"Filter '{filter_obj.keyword}' activated")
            await self.session.commit()
            return True
        return False

    async def deactivate_filter(self, filter_id: int) -> bool:
        """Deactivate filter"""
        result = await self.session.execute(
            update(Filter)
            .where(Filter.id == filter_id)
            .values(active=False)
        )
        
        if result.rowcount > 0:
            filter_obj = await self.get_filter_by_id(filter_id)
            await self._log_activity(filter_obj.supplier_id, "filter_deactivated", f"Filter '{filter_obj.keyword}' deactivated")
            await self.session.commit()
            return True
        return False

    async def bulk_create_filters(self, supplier_id: int, keywords: List[str]) -> List[Filter]:
        """Create multiple filters at once"""
        filters = []
        for keyword in keywords:
            filter_obj = Filter(
                supplier_id=supplier_id,
                keyword=keyword,
                priority=0,
                active=True
            )
            filters.append(filter_obj)
            self.session.add(filter_obj)
        
        await self.session.commit()
        
        await self._log_activity(supplier_id, "filters_bulk_created", f"Created {len(filters)} filters")
        return filters

    async def search_filters(self, keyword: str) -> List[Filter]:
        """Search filters by keyword"""
        result = await self.session.execute(
            select(Filter)
            .where(Filter.keyword.ilike(f"%{keyword}%"))
            .order_by(Filter.keyword)
        )
        return result.scalars().all()

    async def _log_activity(self, user_id: int, action: str, details: str = None):
        """Log user activity"""
        from db.models import ActivityLog
        
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details
        )
        self.session.add(log)
