from typing import Dict, Any, List
import re

# --- Helper 1: Validador de Teléfono (sin cambios) ---
def _validate_phone_ar(phone_str: str) -> bool:
    if not phone_str:
        return False
    cleaned_phone = re.sub(r"[\s\-\(\)\+]", "", phone_str)
    regex = r"^(54)?(9)?(\d{10})$"
    match = re.match(regex, cleaned_phone)
    return bool(match)

# --- Helper 2: Simulador de Geocodificación (v5 - Bounding Box) ---

# Coordenadas REALES (aproximadas) para "cajas" de barrios
# Formato: [lat_min, lon_min, lat_max, lon_max]
BOUNDING_BOXES = {
    # --- PARTIDO DE LA PLATA ---
    "la plata (casco urbano)": [-34.93, -57.97, -34.90, -57.93],
    "altos de san lorenzo":   [-34.95, -57.95, -34.93, -57.92],
    "los hornos":             [-34.96, -57.98, -34.93, -57.94],
    "villa elvira":           [-34.94, -57.92, -34.92, -57.88],
    "tolosa":                 [-34.90, -57.98, -34.88, -57.96],
    "ringuelet":              [-34.88, -57.99, -34.87, -57.97],
    "manuel b. gonnet":       [-34.893, -58.03, -34.87, -58.00],
    "city bell":              [-34.88, -58.07, -34.85, -58.04],
    "villa elisa":            [-34.86, -58.10, -34.83, -58.07],
    "lisandro olmos":         [-34.98, -58.04, -34.95, -58.00],
    "melchor romero":         [-34.96, -58.06, -34.92, -58.00],
    "abasto":                 [-35.00, -58.08, -34.96, -58.02],
    "josé hernández":         [-34.90, -58.03, -34.88, -58.01],
    
    # --- PARTIDO DE BERISSO ---
    "berisso (ciudad)":       [-34.88, -57.89, -34.86, -57.87],
    "villa san carlos":       [-34.89, -57.90, -34.88, -57.88],
    "villa argüello":         [-34.91, -57.93, -34.89, -57.91],
    "villa zula":             [-34.89, -57.91, -34.88, -57.90],
    "barrio universitario":   [-34.905, -57.93, -34.895, -57.92],
    "los talas":              [-34.93, -57.88, -34.89, -57.85],
    "la hermosura":           [-34.98, -57.90, -34.95, -57.87],
    
    # --- PARTIDO DE ENSENADA (Bonus) ---
    "ensenada (ciudad)":      [-34.86, -57.92, -34.84, -57.90],
    "punta lara":             [-34.82, -58.01, -34.78, -57.95],
}

def _simulate_geocoding_neighborhood(lat: float, lon: float) -> str:
    """
    Simula una API de Geocodificación Inversa (v5).
    Comprueba si un (lat, lon) real cae dentro de una de
    nuestras "cajas" (bounding box) de simulación.
    """
    
    # Comprobamos cada "caja"
    for neighborhood, box in BOUNDING_BOXES.items():
        lat_min, lon_min, lat_max, lon_max = box
        
        if (lat_min <= lat <= lat_max) and (lon_min <= lon <= lon_max):
            return neighborhood
            
    # Si no cae en ninguna caja
    return "desconocido"

# --- Función Principal: El Motor v4.0 (Híbrido) ---
# (Esta función no necesita cambios, ya que la lógica
# de _simulate_geocoding_neighborhood está encapsulada)
def validate_stop(stop: Dict[str, Any]) -> Dict[str, Any]:
    """
    Motor de Validación v4.0 (Híbrido)
    """
    errors_list: List[str] = []
    
    cliente_data = {
        "neighborhood": stop.get("neighborhood_cliente", "").lower().strip(),
        "street": stop.get("address_street_cliente", "").lower().strip(),
        "number": stop.get("address_number_cliente", "").lower().strip(),
    }
    
    validation_data_db = stop.get("validation_data", {})
    correct_street_data = {
        "street": validation_data_db.get("correct_street", "").lower().strip(),
        "number": validation_data_db.get("correct_number", "").lower().strip(),
    }
    
    is_phone_valid = validation_data_db.get("is_phone_valid", False)

    # --- LLAMA AL NUEVO SIMULADOR v5 ---
    correct_hood_from_gps = _simulate_geocoding_neighborhood(
        stop.get("gps_lat_cliente", 0),
        stop.get("gps_lon_cliente", 0)
    )

    # --- INICIO DE VALIDACIONES ---
    if not is_phone_valid:
        errors_list.append(f"Teléfono no válido: '{stop.get('phone_cliente', '')}'.")

    if cliente_data["neighborhood"] != correct_hood_from_gps:
        msg = (
            f"¡Conflicto de Barrio! "
            f"Cliente dice '{cliente_data['neighborhood']}', pero GPS indica '{correct_hood_from_gps}'."
        )
        errors_list.append(f"GRAVE: {msg}")

    if cliente_data["street"] != correct_street_data["street"]:
        msg = (
            f"¡Conflicto de Calle! "
            f"Cliente dice '{cliente_data['street']}', pero debería ser '{correct_street_data['street']}'."
        )
        errors_list.append(f"GRAVE: {msg}")

    if cliente_data["number"] != correct_street_data["number"]:
        msg = (
            f"Conflicto de Numeración. "
            f"Cliente dice '{cliente_data['number']}', pero debería ser '{correct_street_data['number']}'."
        )
        errors_list.append(f"MEDIO: {msg}")
    
    if any("GRAVE:" in err for err in errors_list):
        stop["validation_status"] = "RED"
    elif any("MEDIO:" in err for err in errors_list):
        stop["validation_status"] = "YELLOW"
    elif errors_list:
        stop["validation_status"] = "YELLOW"
    else:
        stop["validation_status"] = "GREEN"
        
    stop["validation_message"] = " | ".join(errors_list) or "Validación OK"
    
    return stop