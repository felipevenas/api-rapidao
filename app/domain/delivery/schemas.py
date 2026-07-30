from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DelivererProfileCreate(BaseModel):
    vehicle_type: Optional[str] = Field("motorcycle", description="Tipo de veículo (ex: bike, motorcycle, car)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude inicial (-90 a 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude inicial (-180 a 180)")
    is_available: bool = Field(True, description="Disponibilidade para aceitar entregas")


class DelivererProfileUpdate(BaseModel):
    vehicle_type: Optional[str] = Field(None, description="Tipo de veículo")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude")
    is_available: Optional[bool] = Field(None, description="Disponibilidade")


class LocationPing(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude atual do entregador")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude atual do entregador")
    is_available: Optional[bool] = Field(None, description="Atualizar também o status de disponibilidade")


class DelivererRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    vehicle_type: str
    latitude: float
    longitude: float
    is_available: bool
    is_busy: bool
    last_ping_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AssignmentResult(BaseModel):
    order_id: UUID
    deliverer_id: UUID
    status: str
    message: str
