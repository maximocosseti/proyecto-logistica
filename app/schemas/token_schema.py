from pydantic import BaseModel
from typing import Optional

class TokenData(BaseModel):
    """
    Este es el schema de los datos que guardaremos
    DENTRO del token JWT.
    """
    email: Optional[str] = None

class Token(BaseModel):
    """
    Este es el schema que enviaremos como RESPUESTA
    al cliente (React) cuando el login sea exitoso.
    """
    access_token: str
    token_type: str = "bearer"