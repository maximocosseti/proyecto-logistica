from fastapi import FastAPI
from app.routes import user_routes 
from app.routes import auth_routes
from app.routes import route_routes
from app.routes import stop_routes # <-- Importado (OK)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Dashboard de Validación Logística",
    description="API para el proyecto de validación de paradas.",
    version="0.0.1"
)

origins = [
    "http://localhost:5173",
    "https://logistica-dashboard-react.vercel.app",
    "https://logistica-dashboard-react-kzi2i29v2-thomas-projects-6307dabf.vercel.app",
    "https://logistica-dashboard-react-qhs3px783-thomas-projects-6307dabf.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "¡Bienvenido a la API de Validación Logística!"}

# Incluir los routers
app.include_router(user_routes.router)
app.include_router(auth_routes.router)
app.include_router(route_routes.router)
app.include_router(stop_routes.router) # <-- Incluido (OK)


# --- ¡NUEVO BLOQUE DE DEBUG! ---
# Esto se ejecutará una sola vez cuando Render inicie el servidor.
@app.on_event("startup")
def print_registered_routes():
    print("\n" + "="*30)
    print("--- RUTAS REGISTRADAS EN FASTAPI ---")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path} | Name: {route.name} | Methods: {getattr(route, 'methods', 'N/A')}")
    print("="*30 + "\n")
# --- FIN DEL BLOQUE DE DEBUG ---
