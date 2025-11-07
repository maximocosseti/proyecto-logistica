from fastapi import FastAPI
from app.routes import user_routes 
from app.routes import auth_routes
from app.routes import route_routes
from app.routes import stop_routes

# --- 1. Importa el Middleware de CORS ---
from fastapi.middleware.cors import CORSMiddleware

# Creamos la instancia de la aplicación
app = FastAPI(
    title="Dashboard de Validación Logística",
    description="API para el proyecto de validación de paradas.",
    version="0.0.1"
)

# --- 2. Define los "orígenes" (dominios) permitidos ---
# En nuestro caso, solo la app de React en el puerto 5173
origins = [
    "http://localhost:5173",
]

# --- 3. Añade el Middleware a la app ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Permite estos orígenes
    allow_credentials=True,      # Permite cookies/tokens
    allow_methods=["*"],         # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],         # Permite todos los headers (incluyendo Authorization)
)


# --- Tus Rutas (el resto del archivo sigue igual) ---

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "¡Bienvenido a la API de Validación Logística!"}

app.include_router(user_routes.router)
app.include_router(auth_routes.router)
app.include_router(route_routes.router)
app.include_router(stop_routes.router)