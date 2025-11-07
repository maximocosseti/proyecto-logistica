from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config.settings import settings
from app.schemas.token_schema import TokenData
from app.config.database import collection_user

# --- 1. Configuración de Hashing ---

# Usamos sha256_crypt (no depende de bcrypt)
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con un hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash de una contraseña en texto plano."""
    return pwd_context.hash(password)

# --- 2. Configuración de Creación de Tokens JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crea un nuevo token JWT.
    """
    to_encode = data.copy()
    
    # Establece el tiempo de expiración
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Usa el valor de nuestros settings
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
    to_encode.update({"exp": expire})
    
    # Lee la clave secreta y el algoritmo desde nuestros settings
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

# --- 3. Esquema de Seguridad y Decodificación de Token ---

# Esto le dice a FastAPI "busca el token en la cabecera 'Authorization'
# que venga desde la URL '/token'"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def decode_access_token(token: str) -> TokenData:
    """
    Decodifica el token JWT y devuelve los datos (el email).
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # 'sub' (subject) es donde guardamos nuestro email
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se pudo validar el token (sin subject)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(email=email)
    except JWTError:
        # Si el token está malformado o ha expirado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- 4. La Dependencia "get_current_user" ---

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependencia que valida el token y devuelve el usuario de la BBDD.
    Esto se ejecutará en cada ruta protegida.
    """
    token_data = decode_access_token(token)
    
    user = await collection_user.find_one({"email": token_data.email})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Devolvemos el usuario como un diccionario
    # (nuestra ruta se encargará de validarlo con UserOut)
    return user