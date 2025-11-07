from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional

# --- 1. Sub-Documento de Validación (v4) ---
# Almacena la 'verdad' de la calle (manual) y el estado del teléfono (calculado)
class ValidationDataModel(BaseModel):
    correct_street: str
    correct_number: str
    correct_ref1: Optional[str] = None
    correct_ref2: Optional[str] = None
    
    # Este campo lo calcula el backend (ver stop_routes.py)
    is_phone_valid: bool 

# --- 2. Modelo Principal de la Parada (v4) ---
class StopModel(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    route_id: ObjectId
    
    # --- Datos de la Parada ---
    customer_name: str
    order_in_route: int
    status: str = "PENDIENTE"

    # --- Datos del Cliente ("Sucios") ---
    neighborhood_cliente: str
    phone_cliente: str
    gps_lat_cliente: float
    gps_lon_cliente: float
    address_street_cliente: str
    address_number_cliente: str
    address_ref1_cliente: Optional[str] = None
    address_ref2_cliente: Optional[str] = None

    # --- Datos de Validación (v4) ---
    # Guardamos la 'verdad' de la calle/teléfono
    validation_data: ValidationDataModel
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )