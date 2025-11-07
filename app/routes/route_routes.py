from fastapi import APIRouter, HTTPException, status, Body, Depends, Path
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

# --- Importaciones Clave ---
from app.schemas.route_schema import RouteCreate, RouteOut, RouteAssign
from app.config.database import collection_route, collection_user
from app.core.security import get_current_user

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
    current_user: dict = Depends(get_current_user)
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

# --- ¡NUEVO ENDPOINT AÑADIDO! ---
@router.patch(
    "/{route_id}/assign",
    response_model=RouteOut,
    summary="Asignar una ruta a un nuevo repartidor (Solo Admins)"
)
async def assign_route(
    route_id: str = Path(..., title="El ID de la ruta"),
    assignment: RouteAssign = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Permite a un admin re-asignar el 'owner_id' de una ruta.
    """
    
    # 1. Verificar Permisos de Admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para asignar rutas."
        )
        
    # 2. Validar que la ruta y el usuario existan
    try:
        route_object_id = ObjectId(route_id)
        # Verificamos que el usuario exista en la colección de usuarios
        user = await collection_user.find_one({"_id": ObjectId(assignment.new_owner_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario (repartidor) no encontrado.")
            
        user_object_id = ObjectId(assignment.new_owner_id)
        
    except Exception:
        raise HTTPException(status_code=400, detail="ID de Ruta o Usuario inválido")
    
    # 3. Actualizar la BBDD
    update_result = await collection_route.update_one(
        {"_id": route_object_id},
        {"$set": {"owner_id": user_object_id}}
    )
    
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Ruta con ID {route_id} no encontrada.")
        
    # 4. Devolver la ruta actualizada
    updated_route = await collection_route.find_one({"_id": route_object_id})
    
    if not updated_route:
            raise HTTPException(status_code=404, detail="Ruta no encontrada después de actualizar.")

    updated_route["id"] = str(updated_route["_id"])
    updated_route["owner_id"] = str(updated_route["owner_id"])
    
    return updated_route

# --- ¡NUEVO ENDPOINT AÑADIDO! ---
@router.get(
    "/me",
    response_model=List[RouteOut],
    summary="Obtener las rutas asignadas al usuario actual (repartidor)"
)
async def get_my_routes(
    current_user: dict = Depends(get_current_user)
):
    """
    Devuelve una lista de todas las rutas (Routes)
    asignadas al 'owner_id' del usuario actual.
    """
    
    user_id = current_user.get("_id")
    
    # 1. Buscar todas las rutas que pertenecen a este usuario
    routes_cursor = collection_route.find({"owner_id": user_id})
    
    routes_list = []
    async for route in routes_cursor:
        # Convertimos IDs a strings para el schema RouteOut
        route["id"] = str(route["_id"])
        route["owner_id"] = str(route["owner_id"])
        routes_list.append(route)
        
    return routes_list