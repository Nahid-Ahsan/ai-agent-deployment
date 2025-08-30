from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/travel_booking?authSource=admin")
client = AsyncIOMotorClient(MONGODB_URL)
db = client["travel_booking"]

async def get_database():
    return db