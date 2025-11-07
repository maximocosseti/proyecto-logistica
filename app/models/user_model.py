from pydantic import BaseModel, EmailStr, Field, ConfigDict
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional

class UserModel(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    EmailStr: EmailStr
    hashed_password: str
    full_name: str
    
    role: str = "repartidor"
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
   
    )