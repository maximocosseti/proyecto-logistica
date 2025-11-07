from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from datetime import datetime, timezone 

# Importamos el ESQUEMA (lo que entra y sale de la API)
from app.schemas.user_schema import UserCreate, UserOut

# Importamos la lógica de hashing
from app.core.security import get_password_hash

# Importamos la colección de la base de datos
from app.config.database import collection_user

from app.core.security import get_current_user

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
    new_user_dict = {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc) # Añadimos la fecha manualmente
    }
    
    # 4. Insertar en la base de datos
    insert_result = await collection_user.insert_one(new_user_dict)
    
    # 5. Devolver el usuario recién creado
    created_user = await collection_user.find_one(
        {"_id": insert_result.inserted_id}
    )
    if created_user:
        created_user["id"] = str(created_user["_id"])
    return created_user


# --- Endpoint para OBTENER el Usuario Actual ---
@router.get(
    "/me",
    response_model=UserOut,
    summary="Obtener los datos del usuario actual"
)
async def read_users_me(
    current_user: dict = Depends(get_current_user)
):
    """
    Devuelve los detalles del usuario que está autenticado (logueado).
    """
    
    current_user["id"] = str(current_user["_id"])
    
    return current_user

# --- ¡NUEVO ENDPOINT AÑADIDO! ---
@router.get(
    "/",
    response_model=List[UserOut], # Devuelve una LISTA de usuarios
    summary="Obtener lista de todos los usuarios (Solo Admins)"
)
async def get_all_users(
    current_user: dict = Depends(get_current_user)
):
    """
    Devuelve una lista de todos los usuarios.
    - **Solo los usuarios con rol 'admin' pueden usar esto.**
    """
    
    # 1. Verificar Permisos de Admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta información."
        )
        
    # 2. Buscar todos los usuarios
    users_cursor = collection_user.find()
    
    users_list = []
    async for user in users_cursor:
        # Convertimos el _id a id para el schema UserOut
        user["id"] = str(user["_id"])
        users_list.append(user)
        
    return users_list