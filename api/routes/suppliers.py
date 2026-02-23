from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from ..dependencies import get_db, get_current_admin
from ..models.schemas import SupplierCreate, SupplierUpdate, SupplierResponse, FilterResponse
from db.models import Supplier, Filter, Order
from sqlalchemy import delete, update
from bot.services import SupplierService, FilterService, OrderService


router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/", response_model=List[SupplierResponse])
async def get_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get suppliers with filtering and pagination"""
    supplier_service = SupplierService(db)
    
    # Get suppliers
    suppliers = await supplier_service.get_all_suppliers(active_only=active_only)
    
    # Apply additional filters
    if role:
        suppliers = [s for s in suppliers if s.role == role]
    
    if search:
        search_lower = search.lower()
        suppliers = [s for s in suppliers if search_lower in s.name.lower()]
    
    # Apply pagination
    suppliers = suppliers[skip:skip+limit]
    
    return suppliers


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific supplier by ID"""
    supplier_service = SupplierService(db)
    supplier = await supplier_service.get_supplier_by_id(supplier_id)
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return supplier


@router.post("/", response_model=SupplierResponse)
async def create_supplier(
    supplier: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Create new supplier"""
    supplier_service = SupplierService(db)
    
    telegram_id = supplier.telegram_id or 0
    if telegram_id != 0:
        existing = await supplier_service.get_supplier_by_telegram(telegram_id)
        if existing:
            raise HTTPException(status_code=400, detail="Supplier with this telegram_id already exists")
    
    new_supplier = await supplier_service.create_supplier(
        telegram_id,
        supplier.name,
        supplier.role
    )
    
    return new_supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Update supplier"""
    supplier_service = SupplierService(db)
    
    # Check if supplier exists
    supplier = await supplier_service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Update supplier
    update_data = supplier_update.model_dump(exclude_unset=True)
    
    if update_data:
        if "name" in update_data:
            await supplier_service.update_supplier_name(supplier_id, update_data["name"])
        
        if "active" in update_data:
            if update_data["active"]:
                await supplier_service.activate_supplier(supplier_id)
            else:
                await supplier_service.deactivate_supplier(supplier_id)
        
        if "role" in update_data:
            result = await db.execute(
                update(Supplier)
                .where(Supplier.id == supplier_id)
                .values(role=update_data["role"])
            )
            if result.rowcount > 0:
                await db.commit()
    
    # Return updated supplier
    updated_supplier = await supplier_service.get_supplier_by_id(supplier_id)
    return updated_supplier


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Delete supplier. Removes related filters and unassigns orders first (Core delete does not cascade)."""
    supplier_service = SupplierService(db)
    
    # Check if supplier exists
    supplier = await supplier_service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Core delete does not trigger ORM cascade: unassign orders, delete filters, then supplier
    await db.execute(update(Order).where(Order.supplier_id == supplier_id).values(supplier_id=None))
    await db.execute(delete(Filter).where(Filter.supplier_id == supplier_id))
    result = await db.execute(delete(Supplier).where(Supplier.id == supplier_id))
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    await db.commit()
    
    return {"message": "Supplier deleted successfully"}


@router.post("/{supplier_id}/activate")
async def activate_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Activate supplier"""
    supplier_service = SupplierService(db)
    
    success = await supplier_service.activate_supplier(supplier_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return {"message": "Supplier activated successfully"}


@router.post("/{supplier_id}/deactivate")
async def deactivate_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Deactivate supplier"""
    supplier_service = SupplierService(db)
    
    success = await supplier_service.deactivate_supplier(supplier_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return {"message": "Supplier deactivated successfully"}


@router.get("/{supplier_id}/filters", response_model=List[FilterResponse])
async def get_supplier_filters(
    supplier_id: int,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get supplier's filters"""
    filter_service = FilterService(db)
    
    # Check if supplier exists
    supplier_service = SupplierService(db)
    supplier = await supplier_service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    filters = await filter_service.get_filters_by_supplier(supplier_id, active_only=active_only)
    return filters


@router.get("/{supplier_id}/orders")
async def get_supplier_orders(
    supplier_id: int,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get supplier's orders"""
    # Check if supplier exists
    supplier_service = SupplierService(db)
    supplier = await supplier_service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    order_service = OrderService(db)
    orders = await order_service.get_orders_by_supplier(supplier_id, status=status)
    
    # Apply pagination
    orders = orders[skip:skip+limit]
    
    return orders
