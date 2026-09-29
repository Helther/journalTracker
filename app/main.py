from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.config import DBConfig
from app.db.database import Database

from app.api.v1 import health, logs


app = FastAPI()

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    db = Database(DBConfig())
    db.connect()
    app.state.db = db
    try:
        yield
    finally:
        await db.dispose()


app = FastAPI(lifespan=app_lifespan)

app.include_router(health.router)
app.include_router(logs.router)
