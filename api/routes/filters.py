from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_admin
from ..models.schemas import FilterCreate, FilterUpdate, FilterResponse, FilterBulkCreate
from bot.services import FilterService, SupplierService


router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("/", response_model=List[FilterResponse])
async def get_filters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    supplier_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get filters with filtering and pagination"""
    filter_service = FilterService(db)
    
    if supplier_id:
        # Get filters for specific supplier
        filters = await filter_service.get_filters_by_supplier(supplier_id, active_only=active_only)
    elif search:
        # Search filters by keyword
        filters = await filter_service.search_filters(search)
    else:
        # Get all filters (would need to implement this method)
        # For now, return empty list
        filters = []
    
    # Apply pagination
    filters = filters[skip:skip+limit]
    
    return filters


@router.get("/{filter_id}", response_model=FilterResponse)
async def get_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific filter by ID"""
    filter_service = FilterService(db)
    filter_obj = await filter_service.get_filter_by_id(filter_id)
    
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    return filter_obj


@router.post("/", response_model=FilterResponse)
async def create_filter(
    filter_data: FilterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Create new filter"""
    filter_service = FilterService(db)
    
    # Check if supplier exists
    supplier_service = SupplierService(db)
    supplier = await supplier_service.get_supplier_by_id(filter_data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    new_filter = await filter_service.create_filter(
        filter_data.supplier_id,
        filter_data.keyword,
        filter_data.priority
    )
    
    return new_filter


@router.put("/{filter_id}", response_model=FilterResponse)
async def update_filter(
    filter_id: int,
    filter_update: FilterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Update filter"""
    filter_service = FilterService(db)
    
    # Check if filter exists
    filter_obj = await filter_service.get_filter_by_id(filter_id)
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    # Update filter
    update_data = filter_update.model_dump(exclude_unset=True)
    
    if update_data:
        success = await filter_service.update_filter(
            filter_id,
            update_data.get("keyword"),
            update_data.get("priority")
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update filter")
    
    # Return updated filter
    updated_filter = await filter_service.get_filter_by_id(filter_id)
    return updated_filter


@router.delete("/{filter_id}")
async def delete_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Delete filter"""
    filter_service = FilterService(db)
    
    # Check if filter exists
    filter_obj = await filter_service.get_filter_by_id(filter_id)
    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    success = await filter_service.delete_filter(filter_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete filter")
    
    return {"message": "Filter deleted successfully"}


@router.post("/{filter_id}/activate")
async def activate_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Activate filter"""
    filter_service = FilterService(db)
    
    success = await filter_service.activate_filter(filter_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    return {"message": "Filter activated successfully"}


@router.post("/{filter_id}/deactivate")
async def deactivate_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Deactivate filter"""
    filter_service = FilterService(db)
    
    success = await filter_service.deactivate_filter(filter_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    return {"message": "Filter deactivated successfully"}


@router.post("/bulk", response_model=List[FilterResponse])
async def create_bulk_filters(
    body: FilterBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Create multiple filters at once. Body: { supplier_id: int, keywords: string[] }"""
    filter_service = FilterService(db)
    supplier_service = SupplierService(db)
    supplier = await supplier_service.get_supplier_by_id(body.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not body.keywords:
        raise HTTPException(status_code=400, detail="keywords must be non-empty list")
    filters = await filter_service.bulk_create_filters(body.supplier_id, body.keywords)
    return filters
