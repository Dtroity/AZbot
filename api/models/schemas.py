from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


# Supplier schemas
class SupplierBase(BaseModel):
    telegram_id: int
    name: str
    active: bool = True
    role: str = "supplier"


class SupplierCreate(BaseModel):
    """Создание поставщика: telegram_id опционален (0 до регистрации в боте)."""
    name: str
    telegram_id: Optional[int] = None
    active: bool = True
    role: str = "supplier"

    @field_validator("telegram_id", mode="before")
    @classmethod
    def empty_telegram_to_none(cls, v):
        if v is None or v == "" or v == []:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None


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


class FilterBulkCreate(BaseModel):
    """Тело запроса для массового создания фильтров."""
    supplier_id: int
    keywords: List[str] = []

    @field_validator("supplier_id", mode="before")
    @classmethod
    def coerce_supplier_id(cls, v):
        if v is None or v == "":
            raise ValueError("supplier_id required")
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError("supplier_id must be integer")


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
