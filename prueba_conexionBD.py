import motor.motor_asyncio
import asyncio
import os
from dotenv import load_dotenv

async def test_connection():
    load_dotenv()
    MONGO_URI = os.getenv("MONGODB_URI")

    # Conectar al cluster
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = client.BTG   
    print(await db.command("ping"))
    cliente = await db.clientes.find_one({"_id": "c1"})
    print(cliente)

asyncio.run(test_connection())