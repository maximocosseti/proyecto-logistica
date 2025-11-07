from fastapi import APIRouter, HTTPException, status, Body, Depends, Path
from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from app.core.validator import validate_stop
from app.schemas.stop_schema import StopLocationUpdate
from app.core.validator import _simulate_geocoding_neighborhood

# Importaciones Clave
from app.schemas.stop_schema import StopCreate, StopOut
from app.config.database import collection_stop, collection_route
from app.core.security import get_current_user
from app.core.validator import _validate_phone_ar

router = APIRouter(
    tags=["Stops"],
    dependencies=[Depends(get_current_user)] 
)

@router.post(
    "/routes/{route_id}/stops",
    response_model=StopOut,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir una nueva parada a una ruta (v4) (Solo Admins)"
)
async def create_stop_for_route(
    route_id: str = Path(..., title="El ID de la ruta"),
    stop: StopCreate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva parada (v4) y la asocia a una ruta existente.
    """
    
    # 1. Verificar Permisos (igual)
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para añadir una parada."
        )
        
    # 2. Verificar que la Ruta exista (igual)
    try:
        route_object_id = ObjectId(route_id)
        route = await collection_route.find_one({"_id": route_object_id})
    except Exception:
        raise HTTPException(status_code=400, detail="ID de Ruta inválido")
        
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la ruta con ID {route_id}"
        )
        
    # 3. Crear el diccionario para la BBDD (v4)
    is_phone_valid = _validate_phone_ar(stop.phone_cliente)
    validation_data_dict = stop.validation_data.model_dump()
    validation_data_dict["is_phone_valid"] = is_phone_valid

    new_stop_dict = {
        "route_id": route_object_id,
        "customer_name": stop.customer_name,
        "order_in_route": stop.order_in_route,
        "status": "PENDIENTE",
        "neighborhood_cliente": stop.neighborhood_cliente,
        "phone_cliente": stop.phone_cliente,
        "gps_lat_cliente": stop.gps_lat_cliente,
        "gps_lon_cliente": stop.gps_lon_cliente,
        "address_street_cliente": stop.address_street_cliente,
        "address_number_cliente": stop.address_number_cliente,
        "address_ref1_cliente": stop.address_ref1_cliente,
        "address_ref2_cliente": stop.address_ref2_cliente,
        "validation_data": validation_data_dict,
        "created_at": datetime.now(timezone.utc)
    }
    
    # 4. Insertar en la base de datos
    insert_result = await collection_stop.insert_one(new_stop_dict)
    
    # 5. Devolver la parada recién creada (validada)
    created_stop = await collection_stop.find_one(
        {"_id": insert_result.inserted_id}
    )
    
    if created_stop:
        created_stop = validate_stop(created_stop)
        created_stop["id"] = str(created_stop["_id"])
        created_stop["route_id"] = str(created_stop["route_id"])
        
    return created_stop

# --- Endpoint GET (Donde estaba el error) ---
@router.get(
    "/routes/{route_id}/stops",
    response_model=List[StopOut],
    summary="Obtener todas las paradas VALIDADAS de una ruta"
)
async def get_stops_for_route(
    route_id: str = Path(..., title="El ID de la ruta"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todas las paradas de una ruta específica y
    las enriquece con el estado de validación (Rojo/Amarillo/Verde).
    """
    
    # 1. Validar ruta (igual que antes)
    try:
        route_object_id = ObjectId(route_id)
        route = await collection_route.find_one({"_id": route_object_id})
    except Exception:
        raise HTTPException(status_code=400, detail="ID de Ruta inválido")
        
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la ruta con ID {route_id}"
        )
        
    # --- 2. VERIFICACIÓN DE PERMISOS (CORREGIDA) ---
    # Usamos .get() para evitar KeyErrors si el campo no existe
    is_repartidor = current_user.get("role") == "repartidor"
    route_owner_id = route.get("owner_id")
    user_id = current_user.get("_id")

    if (is_repartidor and route_owner_id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta ruta."
        )
    # -----------------------------------------------
        
    # 3. BUSCAR, VALIDAR Y CONSTRUIR LA RESPUESTA
    stops_cursor = collection_stop.find({"route_id": route_object_id})
    validated_stops_list = []
    
    async for stop in stops_cursor:
        validated_stop = validate_stop(stop)
        validated_stop["id"] = str(validated_stop["_id"])
        validated_stop["route_id"] = str(validated_stop["route_id"])
        validated_stops_list.append(validated_stop)
        
    return validated_stops_list

# (Al final de app/routes/stop_routes.py, 
# después de la función get_stops_for_route)

# (En app/routes/stop_routes.py)

@router.patch(
    "/stops/{stop_id}/location",
    response_model=StopOut, # Devolveremos la parada actualizada y validada
    summary="Actualizar la ubicación GPS de una parada (Feedback Loop)"
)
async def update_stop_location(
    stop_id: str = Path(..., title="El ID de la parada a actualizar"),
    location: StopLocationUpdate = Body(...), # <-- Recibe las nuevas coords
    current_user: dict = Depends(get_current_user)
):
    """
    Implementa el "Bucle de Retroalimentación".
    
    Permite a un usuario (admin o repartidor) actualizar
    las coordenadas GPS de una parada.
    """
    
    # 1. Validar el Stop ID
    try:
        stop_object_id = ObjectId(stop_id)
        stop = await collection_stop.find_one({"_id": stop_object_id})
    except Exception:
        raise HTTPException(status_code=400, detail="ID de Parada inválido")
            
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la parada con ID {stop_id}"
        )
            
    # 2. (Opcional) Verificar Permisos...
    
    # 3. ¡Lógica del Feedback Loop (CORREGIDA)!
    # El repartidor SOLO actualiza el GPS.
    # NO recalculamos el barrio aquí.
    update_data = {
        "$set": {
            "gps_lat_cliente": location.gps_lat_cliente,
            "gps_lon_cliente": location.gps_lon_cliente,
            # ¡Ya NO actualizamos el neighborhood_cliente!
        }
    }
    
    # 4. Ejecutamos la actualización en la BBDD
    await collection_stop.update_one(
        {"_id": stop_object_id},
        update_data
    )
    
    # 5. Obtenemos la parada actualizada
    updated_stop = await collection_stop.find_one({"_id": stop_object_id})
    
    # 6. La validamos y la devolvemos
    if updated_stop:
        # validate_stop AHORA hará la comparación correcta:
        # (ej: 'city bell' vs 'tolosa')
        updated_stop = validate_stop(updated_stop)
        updated_stop["id"] = str(updated_stop["_id"])
        updated_stop["route_id"] = str(updated_stop["route_id"])
            
    return updated_stop