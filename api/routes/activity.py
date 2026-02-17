from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ..dependencies import get_db, get_current_admin
from ..models.schemas import ActivityLogResponse
from db.models import ActivityLog


router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/", response_model=List[ActivityLogResponse])
async def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    hours: Optional[int] = Query(None, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get activity logs with filtering"""
    
    # Build base query
    query = select(ActivityLog).order_by(desc(ActivityLog.created_at))
    
    # Apply filters
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    
    if action:
        query = query.where(ActivityLog.action == action)
    
    if hours:
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(ActivityLog.created_at >= start_date)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs


@router.get("/actions")
async def get_available_actions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get list of available activity actions"""
    
    # Get distinct actions
    result = await db.execute(
        select(ActivityLog.action).distinct().order_by(ActivityLog.action)
    )
    actions = result.scalars().all()
    
    return {"actions": list(actions)}


@router.get("/recent")
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get recent activity across all users"""
    
    result = await db.execute(
        select(ActivityLog)
        .order_by(desc(ActivityLog.created_at))
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return logs


@router.get("/user/{user_id}")
async def get_user_activity(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    hours: Optional[int] = Query(None, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get activity for specific user"""
    
    # Build query
    query = select(ActivityLog).where(ActivityLog.user_id == user_id)
    
    if hours:
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(ActivityLog.created_at >= start_date)
    
    query = query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs
