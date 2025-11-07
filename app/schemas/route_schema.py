from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Esquema base con campos comunes
class RouteBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    status: str = "PENDIENTE"

# Esquema para crear una ruta (lo que recibimos de la API)
class RouteCreate(RouteBase):
    pass # Por ahora, es igual al base

# Esquema para la respuesta de la API (lo que devolvemos)
class RouteOut(RouteBase):
    id: str
    owner_id: str # Devolveremos el ID del dueño como string
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes = True
    )

# --- ¡NUEVA CLASE AÑADIDA! ---
class RouteAssign(BaseModel):
    """
    Schema para recibir el ID del nuevo dueño de la ruta.
    """
    new_owner_id: str