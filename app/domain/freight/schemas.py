from pydantic import BaseModel, ConfigDict, Field


class FreightRequest(BaseModel):
    """Schema de entrada para cálculo de frete por geolocalização."""
    store_latitude: float = Field(..., description="Latitude da loja de origem")
    store_longitude: float = Field(..., description="Longitude da loja de origem")
    delivery_latitude: float = Field(..., description="Latitude do endereço de entrega")
    delivery_longitude: float = Field(..., description="Longitude do endereço de entrega")

    model_config = ConfigDict(from_attributes=True)


class FreightResponse(BaseModel):
    """Schema de resposta com distância calculada e valor do frete."""
    distance_km: float = Field(..., description="Distância em quilômetros entre origem e destino")
    freight_value: float = Field(..., description="Valor do frete calculado em reais")

    model_config = ConfigDict(from_attributes=True)
