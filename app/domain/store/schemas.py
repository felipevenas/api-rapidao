from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.product.schemas import ProductRead


class StoreBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    address: Optional[str] = None
    latitude: float
    longitude: float


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class StoreRead(StoreBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MenuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    store_id: UUID
    store_name: str
    store_category: Optional[str] = None
    is_active: bool
    products: List[ProductRead]
