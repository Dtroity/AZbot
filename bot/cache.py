from typing import Any, Optional, List
from datetime import timedelta
from .redis_client import redis_client

class CacheService:
    """Service for caching data in Redis"""
    
    CACHE_KEYS = {
        'SUPPLIERS': 'suppliers:active',
        'FILTERS': 'filters:supplier:{supplier_id}',
        'ORDER_STATS': 'stats:orders:{period}',
        'SUPPLIER_PERFORMANCE': 'stats:suppliers:performance',
        'USER_SESSION': 'session:user:{user_id}',
        'ORDER_CACHE': 'order:{order_id}',
        'SUPPLIER_ORDERS': 'orders:supplier:{supplier_id}',
    }
    
    CACHE_TTL = {
        'SHORT': 300,  # 5 minutes
        'MEDIUM': 1800,  # 30 minutes
        'LONG': 3600,  # 1 hour
        'DAILY': 86400,  # 24 hours
    }
    
    @staticmethod
    async def get_active_suppliers() -> Optional[List[dict]]:
        """Get cached active suppliers"""
        return await redis_client.get(CacheService.CACHE_KEYS['SUPPLIERS'])
    
    @staticmethod
    async def set_active_suppliers(suppliers: List[dict]) -> bool:
        """Cache active suppliers"""
        return await redis_client.set(
            CacheService.CACHE_KEYS['SUPPLIERS'],
            suppliers,
            CacheService.CACHE_TTL['MEDIUM']
        )
    
    @staticmethod
    async def get_supplier_filters(supplier_id: int) -> Optional[List[dict]]:
        """Get cached supplier filters"""
        key = CacheService.CACHE_KEYS['FILTERS'].format(supplier_id=supplier_id)
        return await redis_client.get(key)
    
    @staticmethod
    async def set_supplier_filters(supplier_id: int, filters: List[dict]) -> bool:
        """Cache supplier filters"""
        key = CacheService.CACHE_KEYS['FILTERS'].format(supplier_id=supplier_id)
        return await redis_client.set(
            key,
            filters,
            CacheService.CACHE_TTL['MEDIUM']
        )
    
    @staticmethod
    async def invalidate_supplier_filters(supplier_id: int) -> bool:
        """Invalidate supplier filters cache"""
        key = CacheService.CACHE_KEYS['FILTERS'].format(supplier_id=supplier_id)
        return await redis_client.delete(key)
    
    @staticmethod
    async def get_order_stats(period: str) -> Optional[dict]:
        """Get cached order statistics"""
        key = CacheService.CACHE_KEYS['ORDER_STATS'].format(period=period)
        return await redis_client.get_json(key)
    
    @staticmethod
    async def set_order_stats(period: str, stats: dict) -> bool:
        """Cache order statistics"""
        key = CacheService.CACHE_KEYS['ORDER_STATS'].format(period=period)
        return await redis_client.set_json(
            key,
            stats,
            CacheService.CACHE_TTL['SHORT']
        )
    
    @staticmethod
    async def get_supplier_performance() -> Optional[List[dict]]:
        """Get cached supplier performance"""
        return await redis_client.get(CacheService.CACHE_KEYS['SUPPLIER_PERFORMANCE'])
    
    @staticmethod
    async def set_supplier_performance(performance: List[dict]) -> bool:
        """Cache supplier performance"""
        return await redis_client.set(
            CacheService.CACHE_KEYS['SUPPLIER_PERFORMANCE'],
            performance,
            CacheService.CACHE_TTL['MEDIUM']
        )
    
    @staticmethod
    async def get_user_session(user_id: int) -> Optional[dict]:
        """Get cached user session"""
        key = CacheService.CACHE_KEYS['USER_SESSION'].format(user_id=user_id)
        return await redis_client.get(key)
    
    @staticmethod
    async def set_user_session(user_id: int, session: dict) -> bool:
        """Cache user session"""
        key = CacheService.CACHE_KEYS['USER_SESSION'].format(user_id=user_id)
        return await redis_client.set(
            key,
            session,
            CacheService.CACHE_TTL['LONG']
        )
    
    @staticmethod
    async def invalidate_user_session(user_id: int) -> bool:
        """Invalidate user session cache"""
        key = CacheService.CACHE_KEYS['USER_SESSION'].format(user_id=user_id)
        return await redis_client.delete(key)
    
    @staticmethod
    async def get_order(order_id: str) -> Optional[dict]:
        """Get cached order"""
        key = CacheService.CACHE_KEYS['ORDER_CACHE'].format(order_id=order_id)
        return await redis_client.get(key)
    
    @staticmethod
    async def set_order(order_id: str, order: dict) -> bool:
        """Cache order"""
        key = CacheService.CACHE_KEYS['ORDER_CACHE'].format(order_id=order_id)
        return await redis_client.set(
            key,
            order,
            CacheService.CACHE_TTL['MEDIUM']
        )
    
    @staticmethod
    async def invalidate_order(order_id: str) -> bool:
        """Invalidate order cache"""
        key = CacheService.CACHE_KEYS['ORDER_CACHE'].format(order_id=order_id)
        return await redis_client.delete(key)
    
    @staticmethod
    async def get_supplier_orders(supplier_id: int) -> Optional[List[dict]]:
        """Get cached supplier orders"""
        key = CacheService.CACHE_KEYS['SUPPLIER_ORDERS'].format(supplier_id=supplier_id)
        return await redis_client.get(key)
    
    @staticmethod
    async def set_supplier_orders(supplier_id: int, orders: List[dict]) -> bool:
        """Cache supplier orders"""
        key = CacheService.CACHE_KEYS['SUPPLIER_ORDERS'].format(supplier_id=supplier_id)
        return await redis_client.set(
            key,
            orders,
            CacheService.CACHE_TTL['SHORT']
        )
    
    @staticmethod
    async def invalidate_supplier_orders(supplier_id: int) -> bool:
        """Invalidate supplier orders cache"""
        key = CacheService.CACHE_KEYS['SUPPLIER_ORDERS'].format(supplier_id=supplier_id)
        return await redis_client.delete(key)
    
    @staticmethod
    async def increment_counter(counter_name: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        return await redis_client.increment(f"counter:{counter_name}", amount)
    
    @staticmethod
    async def get_counter(counter_name: str) -> Optional[int]:
        """Get counter value"""
        try:
            value = await redis_client.get(f"counter:{counter_name}")
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    async def clear_all_cache() -> bool:
        """Clear all cache (use with caution!)"""
        try:
            keys = await redis_client.keys("cache:*")
            if keys:
                await redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Clear cache error: {e}")
            return False
