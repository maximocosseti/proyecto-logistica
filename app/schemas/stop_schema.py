from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# --- Esquema para el sub-documento de validación (v4) ---
# Esto es lo que pedimos en el POST: solo la 'verdad' de la calle
class ValidationDataIn(BaseModel):
    correct_street: str
    correct_number: str
    correct_ref1: Optional[str] = None
    correct_ref2: Optional[str] = None
    # Ya no pedimos 'correct_neighborhood' ni 'is_phone_valid'

# --- Esquema base de la Parada (v4) ---
class StopBase(BaseModel):
    customer_name: str
    order_in_route: int
    
    # --- Datos del Cliente ("Sucios") ---
    neighborhood_cliente: str
    phone_cliente: str
    gps_lat_cliente: float # <-- El GPS sigue siendo del cliente
    gps_lon_cliente: float
    
    address_street_cliente: str
    address_number_cliente: str
    address_ref1_cliente: Optional[str] = None
    address_ref2_cliente: Optional[str] = None

# --- Esquema para CREAR una parada (v4) ---
class StopCreate(StopBase):
    # Requerimos los datos de validación (solo calle/nro)
    validation_data: ValidationDataIn

# --- Esquema para la respuesta de la API (v4) ---
# Definimos qué datos de validación mostramos (opcional pero limpio)
class ValidationDataOut(BaseModel):
    correct_street: str
    correct_number: str
    correct_ref1: Optional[str] = None
    correct_ref2: Optional[str] = None
    is_phone_valid: bool
    
class StopOut(StopBase):
    id: str
    route_id: str
    status: str
    created_at: datetime
    
    # Devolvemos los datos de validación que se guardaron
    validation_data: ValidationDataOut
    
    # Estos campos los AÑADE el motor de validación
    validation_status: str
    validation_message: str
    
    model_config = ConfigDict(
        from_attributes = True
    )

class StopLocationUpdate(BaseModel):
    """
    Schema para recibir la actualización de coordenadas
    desde el pin arrastrable del mapa.
    """
    gps_lat_cliente: float
    gps_lon_cliente: float