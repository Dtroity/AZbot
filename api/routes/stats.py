from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ..dependencies import get_db, get_current_admin
from ..models.schemas import StatsResponse, OrderStats, SupplierStats
from db.models import Order, Supplier, ActivityLog


router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/", response_model=StatsResponse)
async def get_stats(
    period: str = Query("today", regex="^(today|week|month|all)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get system statistics for specified period"""
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # all
        start_date = None
    
    # Get order statistics
    order_stats = await get_order_stats(db, start_date)
    
    # Get supplier statistics
    supplier_stats = await get_supplier_stats(db)
    
    return StatsResponse(
        orders=order_stats,
        suppliers=supplier_stats,
        period=period
    )


async def get_order_stats(db: AsyncSession, start_date: datetime = None) -> OrderStats:
    """Get order statistics"""
    
    # Build base query
    query = select(Order)
    if start_date:
        query = query.where(Order.created_at >= start_date)
    
    # Get total orders
    result = await db.execute(select(func.count(Order.id)).select_from(query.subquery()))
    total = result.scalar() or 0
    
    # Get orders by status
    status_query = select(Order.status, func.count(Order.id)).select_from(query.subquery()).group_by(Order.status)
    status_result = await db.execute(status_query)
    status_counts = dict(status_result.all())
    
    completed = status_counts.get("COMPLETED", 0)
    pending = status_counts.get("NEW", 0) + status_counts.get("ASSIGNED", 0) + status_counts.get("ACCEPTED", 0)
    cancelled = status_counts.get("DECLINED", 0) + status_counts.get("CANCELLED", 0)
    
    # Calculate completion rate
    completion_rate = (completed / total * 100) if total > 0 else 0.0
    
    return OrderStats(
        total=total,
        completed=completed,
        pending=pending,
        cancelled=cancelled,
        completion_rate=completion_rate
    )


async def get_supplier_stats(db: AsyncSession) -> SupplierStats:
    """Get supplier statistics"""
    
    # Get total suppliers
    total_result = await db.execute(select(func.count(Supplier.id)))
    total = total_result.scalar() or 0
    
    # Get active suppliers
    active_result = await db.execute(
        select(func.count(Supplier.id)).where(Supplier.active == True)
    )
    active = active_result.scalar() or 0
    
    # Inactive suppliers
    inactive = total - active
    
    return SupplierStats(
        total=total,
        active=active,
        inactive=inactive
    )


@router.get("/orders/daily")
async def get_daily_order_stats(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get daily order statistics for the last N days"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days-1)
    
    # Get daily order counts
    daily_stats = await db.execute(
        select(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count')
        )
        .where(Order.created_at >= start_date)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    
    daily_data = daily_stats.all()
    
    # Fill missing dates with zero
    result = []
    current_date = start_date.date()
    
    for i in range(days):
        date_str = current_date.isoformat()
        count = 0
        
        for date, cnt in daily_data:
            if date.date() == current_date:
                count = cnt
                break
        
        result.append({
            "date": date_str,
            "count": count
        })
        
        current_date += timedelta(days=1)
    
    return result


@router.get("/suppliers/performance")
async def get_supplier_performance(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get supplier performance statistics"""
    
    # Get supplier performance data
    performance_query = select(
        Supplier.id,
        Supplier.name,
        func.count(Order.id).label('total_orders'),
        func.sum(func.case((Order.status == 'COMPLETED', 1), else_=0)).label('completed_orders'),
        func.sum(func.case((Order.status == 'DECLINED', 1), else_=0)).label('declined_orders')
    ).outerjoin(Order, Supplier.id == Order.supplier_id).group_by(Supplier.id, Supplier.name)
    
    result = await db.execute(performance_query)
    suppliers_data = result.all()
    
    # Calculate performance metrics
    performance_list = []
    for supplier_id, name, total, completed, declined in suppliers_data:
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        
        performance_list.append({
            "supplier_id": supplier_id,
            "name": name,
            "total_orders": total or 0,
            "completed_orders": completed or 0,
            "declined_orders": declined or 0,
            "completion_rate": completion_rate
        })
    
    # Sort by completion rate and limit
    performance_list.sort(key=lambda x: x["completion_rate"], reverse=True)
    performance_list = performance_list[:limit]
    
    return performance_list


@router.get("/activity")
async def get_activity_stats(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get recent activity statistics"""
    
    start_date = datetime.utcnow() - timedelta(hours=hours)
    
    # Get activity counts by action
    activity_query = select(
        ActivityLog.action,
        func.count(ActivityLog.id).label('count')
    ).where(
        ActivityLog.created_at >= start_date
    ).group_by(ActivityLog.action)
    
    result = await db.execute(activity_query)
    activity_data = dict(result.all())
    
    # Get hourly activity
    hourly_query = select(
        func.date_trunc('hour', ActivityLog.created_at).label('hour'),
        func.count(ActivityLog.id).label('count')
    ).where(
        ActivityLog.created_at >= start_date
    ).group_by(func.date_trunc('hour', ActivityLog.created_at)).order_by('hour')
    
    hourly_result = await db.execute(hourly_query)
    hourly_data = [
        {
            "hour": hour.isoformat() if hour else None,
            "count": count
        }
        for hour, count in hourly_result.all()
    ]
    
    return {
        "period_hours": hours,
        "action_counts": activity_data,
        "hourly_activity": hourly_data
    }


@router.get("/orders/status-distribution")
async def get_order_status_distribution(
    period: str = Query("today", regex="^(today|week|month|all)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get order status distribution for specified period"""
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # all
        start_date = None
    
    # Build query
    query = select(Order.status, func.count(Order.id))
    if start_date:
        query = query.where(Order.created_at >= start_date)
    
    query = query.group_by(Order.status)
    
    result = await db.execute(query)
    status_data = dict(result.all())
    
    # Format for charts
    distribution = [
        {"status": status, "count": count}
        for status, count in status_data.items()
    ]
    
    return {
        "period": period,
        "distribution": distribution
    }
