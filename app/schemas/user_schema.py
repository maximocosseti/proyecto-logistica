from pydantic import BaseModel, EmailStr, Field, ConfigDict # <-- Importamos ConfigDict
from bson import ObjectId
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "admin"
    is_active: bool = True
    
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
class UserOut(UserBase):
    id: str
    created_at: datetime
    
    # --- ESTA ES LA SINTAXIS V2 CORRECTA ---
    model_config = ConfigDict(
        from_attributes = True 
    )

class UserInDB(UserBase):
    id: ObjectId = Field(alias="_id")
    hashed_password: str
    created_at: datetime
    
    # --- ESTA ES LA SINTAXIS V2 CORRECTA ---
    model_config = ConfigDict(
        from_attributes = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str}
    )