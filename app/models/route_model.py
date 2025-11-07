from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional

class RouteModel(BaseModel):
    
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    
    owner_id: ObjectId
    
    name: str = Field(..., min_length=3)
    
    status: str = "PENDIENTE" 
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
    