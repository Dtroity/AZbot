from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from sqlalchemy import func

from ..dependencies import get_db, get_current_admin
from ..models.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, OrderListPaginatedResponse, OrderMessageResponse
from db.models import Order
from bot.services import OrderService, MessageService


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=OrderListPaginatedResponse)
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    admin_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get orders with filtering and pagination. Returns items and total count."""
    # Base conditions
    conditions = []
    if status:
        conditions.append(Order.status == status)
    if supplier_id:
        conditions.append(Order.supplier_id == supplier_id)
    if admin_id:
        conditions.append(Order.admin_id == admin_id)
    if search:
        conditions.append(Order.text.ilike(f"%{search}%"))

    # Total count (same filters, no pagination)
    count_q = select(func.count(Order.id)).where(*conditions) if conditions else select(func.count(Order.id))
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Paginated list
    query = select(Order).options(selectinload(Order.supplier))
    if conditions:
        query = query.where(*conditions)
    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    return {"items": orders, "total": total}


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific order by ID"""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Create new order"""
    order_service = OrderService(db)
    
    # Override admin_id with current user
    order_data = order.model_dump()
    order_data["admin_id"] = current_user["id"]
    
    new_order = await order_service.create_order(order_data["text"], order_data["admin_id"])
    
    # Load full order with relationships
    created_order = await order_service.get_order(new_order.id)
    
    return created_order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Update order"""
    order_service = OrderService(db)
    
    # Check if order exists
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update order
    update_data = order_update.model_dump(exclude_unset=True)
    
    if update_data:
        from sqlalchemy import update
        from datetime import datetime
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(**update_data)
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        await db.commit()
    
    # Return updated order
    updated_order = await order_service.get_order(order_id)
    return updated_order


@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Delete order"""
    order_service = OrderService(db)
    
    # Check if order exists
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Delete order
    from sqlalchemy import delete
    
    result = await db.execute(
        delete(Order).where(Order.id == order_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    await db.commit()
    
    return {"message": "Order deleted successfully"}


@router.get("/{order_id}/messages", response_model=List[OrderMessageResponse])
async def get_order_messages(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for order"""
    message_service = MessageService(db)
    messages = await message_service.get_order_messages(order_id)
    return messages


@router.post("/{order_id}/messages", response_model=OrderMessageResponse)
async def add_order_message(
    order_id: str,
    message_text: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Add message to order"""
    order_service = OrderService(db)
    message_service = MessageService(db)
    
    # Check if order exists
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Add message
    message = await message_service.send_message(
        order_id, 
        current_user["id"], 
        message_text
    )
    
    return message


@router.post("/{order_id}/accept")
async def accept_order(
    order_id: str,
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Accept order (for suppliers)"""
    order_service = OrderService(db)
    
    success = await order_service.accept_order(order_id, supplier_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to accept order")
    
    return {"message": "Order accepted successfully"}


@router.post("/{order_id}/decline")
async def decline_order(
    order_id: str,
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Decline order (for suppliers)"""
    order_service = OrderService(db)
    
    success = await order_service.decline_order(order_id, supplier_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to decline order")
    
    return {"message": "Order declined successfully"}


@router.post("/{order_id}/complete")
async def complete_order(
    order_id: str,
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Complete order (for suppliers)"""
    order_service = OrderService(db)
    
    success = await order_service.complete_order(order_id, supplier_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to complete order")
    
    return {"message": "Order completed successfully"}


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel order (for suppliers)"""
    order_service = OrderService(db)
    
    success = await order_service.cancel_order(order_id, supplier_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel order")
    
    return {"message": "Order cancelled successfully"}
