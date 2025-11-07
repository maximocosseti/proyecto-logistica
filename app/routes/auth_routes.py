from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from datetime import timedelta

# Importamos nuestras funciones de seguridad
# ¡¡AÑADIMOS 'verify_password' aquí para el debug!!
from app.core.security import verify_password, create_access_token
# Importamos la configuración
from app.config.settings import settings
# Importamos la colección de la base de datos
from app.config.database import collection_user
# Importamos nuestro schema de respuesta
from app.schemas.token_schema import Token

router = APIRouter(
    tags=["Auth"] # Lo agrupamos en "Auth" en los /docs
)

@router.post(
    "/token", 
    response_model=Token,
    summary="Iniciar sesión y obtener un token de acceso"
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> dict[str, Any]:
    """
    Endpoint de login.
    """
    
    # 1. Buscar al usuario
    user = await collection_user.find_one({"email": form_data.username})
    
    # --- INICIO DEL BLOQUE DE DEBUG ---
    print("="*30)
    print(f"--- DEBUG: Intentando login para: {form_data.username}")
    
    if user:
        print(f"--- DEBUG: Usuario encontrado en BBDD.")
        print(f"--- DEBUG: Password recibido (front): '{form_data.password}'")
        print(f"--- DEBUG: Hash guardado (BBDD):     '{user.get('hashed_password', '¡¡CAMPO HASHED_PASSWORD NO ENCONTRADO!!')}'")
        
        # Verificamos la contraseña aquí MISMO
        is_password_correct = verify_password(form_data.password, user.get("hashed_password", ""))
        print(f"--- DEBUG: ¿La verificación es exitosa?: {is_password_correct}")
        
    else:
        print(f"--- DEBUG: Usuario NO encontrado en BBDD.")
    
    print("="*30)
    # --- FIN DEL BLOQUE DE DEBUG ---

    # 2. Lógica de Verificación Real
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Crear el token JWT
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token_data = {"sub": user["email"]}
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}