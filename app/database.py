from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


class _DB:
    def __init__(self):
        self._client = None
        self._db = None

    def _ensure(self):
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.MONGODB_URI)
            self._db = self._client.sheetkaizen
            print("✅ Connesso a MongoDB Atlas - SheetKaizen")

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("❌ Disconnesso da MongoDB")

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        self._ensure()
        return getattr(self._db, name)


db = _DB()


async def connect_db():
    db._ensure()


async def close_db():
    db.close()
