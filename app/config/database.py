from motor.motor_asyncio import AsyncIOMotorClient
from .settings import settings

client = AsyncIOMotorClient(settings.MONGO_URL)

db = client[settings.MONGO_DB_NAME]   

collection_user = db["users"]
collection_route = db["routes"]
collection_stop = db["stops"]