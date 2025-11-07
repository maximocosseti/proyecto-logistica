from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from datetime import datetime, timezone

# --- Importaciones Clave ---
from app.schemas.route_schema import RouteCreate, RouteOut
from app.config.database import collection_route
from app.core.security import get_current_user # <-- Nuestra dependencia

router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
    # Protegemos TODAS las rutas de este router
    dependencies=[Depends(get_current_user)] 
)

@router.post(
    "/",
    response_model=RouteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva ruta (Solo Admins)"
)
async def create_route(
    route: RouteCreate = Body(...),
    current_user: dict = Depends(get_current_user) # <-- Inyectamos al usuario
):
    """
    Crea una nueva ruta de reparto.
    
    - **Solo los usuarios con rol 'admin' pueden crear rutas.**
    - El 'owner_id' (repartidor) se asignará al usuario que la crea,
      pero un admin podría modificarlo después (función futura).
    """
    
    # 1. Verificar Permisos (¡NUEVO!)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear una ruta."
        )
        
    # 2. Crear el diccionario para la BBDD
    new_route_dict = {
        "name": route.name,
        "status": route.status,
        "owner_id": current_user["_id"], # Asignamos al admin que la crea
        "created_at": datetime.now(timezone.utc)
    }
    
    # 3. Insertar en la base de datos
    insert_result = await collection_route.insert_one(new_route_dict)
    
    # 4. Devolver la ruta recién creada
    created_route = await collection_route.find_one(
        {"_id": insert_result.inserted_id}
    )
    
    if created_route:
        # Convertimos IDs a strings para el schema RouteOut
        created_route["id"] = str(created_route["_id"])
        created_route["owner_id"] = str(created_route["owner_id"])
        
    return created_route