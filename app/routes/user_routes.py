from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from datetime import datetime, timezone # <-- 1. Importamos datetime

# Importamos el ESQUEMA (lo que entra y sale de la API)
from app.schemas.user_schema import UserCreate, UserOut

# Importamos la lógica de hashing
from app.core.security import get_password_hash

# Importamos la colección de la base de datos
from app.config.database import collection_user

from app.core.security import get_current_user

from fastapi import Depends

# (Ya no importamos UserModel, es lo que está fallando)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario"
)

async def create_user(user: UserCreate = Body(...)):
    """
    Crea un nuevo usuario en la base de datos.
    """
    
    # 1. Verificar si el email ya existe
    existing_user = await collection_user.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya se encuentra registrado."
        )
        
    # 2. Hashear la contraseña (Esto ya funciona)
    hashed_password = get_password_hash(user.password)
    
    # 3. Crear el documento para la BBDD (MODO MANUAL)
    # ------------------------------------------------------------------
    # --- ESTA ES LA SOLUCIÓN ---
    # En lugar de usar UserModel (que falla), creamos un dict simple.
    new_user_dict = {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc) # Añadimos la fecha manualmente
    }
    # ------------------------------------------------------------------
    
    # 4. Insertar en la base de datos
    insert_result = await collection_user.insert_one(new_user_dict)
    
    # 5. Devolver el usuario recién creado
    # Lo buscamos por su nuevo ID para devolver el documento completo
    created_user = await collection_user.find_one(
        {"_id": insert_result.inserted_id}
    )
    if created_user:
        created_user["id"] = str(created_user["_id"])
    # FastAPI usará UserOut para filtrar la respuesta (esto sí funciona)
    return created_user


# --- Endpoint para OBTENER el Usuario Actual ---
@router.get(
    "/me",
    response_model=UserOut,
    summary="Obtener los datos del usuario actual"
)
async def read_users_me(
    # Aquí FastAPI "inyecta" al usuario validado
    current_user: dict = Depends(get_current_user)
):
    """
    Devuelve los detalles del usuario que está autenticado (logueado).
    Necesita un token JWT válido en la cabecera 'Authorization: Bearer {token}'.
    """
    
    # El 'current_user' que recibimos es un dict de la BBDD.
    # Tenemos que añadirle el campo 'id' (string) para que
    # 'UserOut' (response_model) pueda validarlo.
    current_user["id"] = str(current_user["_id"])
    
    return current_user