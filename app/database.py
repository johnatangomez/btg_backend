import motor.motor_asyncio
import os
from app.config import MONGODB_URI
from app.logger import logger

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    db = client.BTG
    logger.info("Conexión a MongoDB establecida")
except Exception as e:
    logger.error(f"Error conectando a MongoDB: {str(e)}")
    raise