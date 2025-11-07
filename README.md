# API de Validación Logística (FastAPI & MongoDB)

Este repositorio contiene el **backend (API REST)** del proyecto de Dashboard de Validación Logística. Es una API segura y asíncrona construida con FastAPI, diseñada para gestionar y validar paradas de rutas de entrega de "última milla".

La funcionalidad principal es un **motor de validación "inteligente"** que simula la geocodificación inversa para detectar paradas "sospechosas" (conflictos de GPS vs. dirección) y las marca con un sistema de semáforo (Rojo/Amarillo/Verde) antes de ser consumidas por un frontend.

---

## Características Principales

* **Autenticación Segura:** Endpoints protegidos usando `OAuth2PasswordBearer` y tokens **JWT**.
* **Hashing de Contraseñas:** `Passlib` (con `sha256_crypt`) para almacenar contraseñas de forma segura.
* **Roles de Usuario:** Lógica de permisos implementada para `admin` (crear rutas/paradas) y `repartidor` (ver sus rutas/corregir paradas).
* **Motor de Validación Híbrido:**
    * **Geocodificación Inversa (Simulada):** Compara `(lat, lon)` con "cajas" geográficas (Bounding Boxes) de barrios para detectar conflictos de ubicación.
    * **Validación Manual:** Compara los datos de calle/número del cliente con una "verdad" ingresada por un admin.
    * **Validación de Datos:** Usa `RegEx` para validar formatos de teléfono (Argentina).
* **Bucle de Retroalimentación:** Endpoint `PATCH` que permite a los repartidores corregir la ubicación GPS de una parada, implementando la lógica de negocio central.
* **Asincronía:** Operaciones de base de datos totalmente asíncronas usando `Motor` y `async/await`.

---

## 💻 Stack Tecnológico

* **Python 3.11+**
* **FastAPI** (para el servidor API)
* **MongoDB** (Base de datos NoSQL)
* **Motor** (Driver asíncrono de MongoDB)
* **Pydantic** (Para validación y schemas de datos)
* **Passlib & python-jose** (Para seguridad, hashing y JWT)
* **Uvicorn** (Servidor ASGI)

---

## 📦 Instalación y Ejecución

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/maximocosseti/proyecto-logistica.git](https://github.com/maximocosseti/proyecto-logistica.git)
    cd proyecto-logistica
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno:**
    * Crea un archivo `.env` en la raíz del proyecto.
    * Copia el contenido de `.env.example` (si existe) o usa la siguiente plantilla:

    ```ini
    # Variables de Base de Datos
    MONGO_URL=mongodb://localhost:27017
    MONGO_DB_NAME=logistica_db

    # Variables de Seguridad (JWT)
    # Genera una clave con: python -c 'import secrets; print(secrets.token_hex(32))'
    SECRET_KEY=TU_CLAVE_SECRETA_AQUI
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

5.  **Ejecutar la Base de Datos:**
    * Asegúrate de que tu servicio de MongoDB (v6.0+) esté corriendo en `localhost:27017`.

6.  **Ejecutar la API:**
    ```bash
    uvicorn app.main:app --reload --reload-dir app
    ```
    * La API estará disponible en `http://127.0.0.1:8000`
    * La documentación (Swagger) está en `http://127.0.0.1:8000/docs`

---

## Endpoints Principales

* `POST /token`: Login (obtiene token JWT).
* `POST /users/`: Registrar un nuevo usuario.
* `GET /users/me`: Obtener datos del usuario logueado (Protegido).
* `POST /routes/`: Crear una nueva ruta (Solo Admin).
* `GET /routes/me`: Obtener rutas asignadas al repartidor (Protegido).
* `POST /routes/{route_id}/stops`: Añadir una parada a una ruta (Solo Admin).
* `GET /routes/{route_id}/stops`: Obtener todas las paradas (con validación) de una ruta (Protegido por Rol).
* `PATCH /stops/{stop_id}/location`: Actualizar la ubicación GPS de una parada (Protegido).