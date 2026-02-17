from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# Supplier schemas
class SupplierBase(BaseModel):
    telegram_id: int
    name: str
    active: bool = True
    role: str = "supplier"


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    role: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Filter schemas
class FilterBase(BaseModel):
    keyword: str
    active: bool = True
    priority: int = 0


class FilterCreate(FilterBase):
    supplier_id: int


class FilterUpdate(BaseModel):
    keyword: Optional[str] = None
    active: Optional[bool] = None
    priority: Optional[int] = None


class FilterResponse(FilterBase):
    id: int
    supplier_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Order schemas
class OrderBase(BaseModel):
    text: str
    status: str = "NEW"
    supplier_id: Optional[int] = None


class OrderCreate(BaseModel):
    text: str
    admin_id: int


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    supplier_id: Optional[int] = None


class OrderResponse(OrderBase):
    id: str
    admin_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None
    messages: List["OrderMessageResponse"] = []
    
    class Config:
        from_attributes = True


# Order Message schemas
class OrderMessageBase(BaseModel):
    message_text: str
    message_type: str = "text"


class OrderMessageResponse(OrderMessageBase):
    id: int
    order_id: str
    sender_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Activity Log schemas
class ActivityLogBase(BaseModel):
    user_id: int
    action: str
    details: Optional[str] = None


class ActivityLogResponse(ActivityLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Stats schemas
class OrderStats(BaseModel):
    total: int
    completed: int
    pending: int
    cancelled: int
    completion_rate: float


class SupplierStats(BaseModel):
    total: int
    active: int
    inactive: int


class StatsResponse(BaseModel):
    orders: OrderStats
    suppliers: SupplierStats
    period: str


# Update forward references
OrderResponse.model_rebuild()
