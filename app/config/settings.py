from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Define y carga las variables de entorno de la aplicación.
    Lee automáticamente desde el archivo .env
    """
    
    # --- Variables de Base de Datos ---
    MONGO_URL: str
    MONGO_DB_NAME: str

    # --- Variables de Seguridad (JWT) ---
    # Las que acabamos de definir para 'security.py'
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # Le dice a Pydantic que lea el archivo .env
        env_file = ".env"

# Creamos una instancia única de la clase Settings.
# Este es el objeto 'settings' que importamos en 
# todos los demás archivos.
settings = Settings()