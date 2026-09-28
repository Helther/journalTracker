from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.config import DBConfig
from app.db.database import Database


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


@app.get("/health")
async def health():
    ok = await app.state.db.healthcheck()
    return {"status": "ok" if ok else "fail"}

@app.get("/api/v1/logs") # get logs based on app
async def logs_get():
    return {}
@app.post("/api/v1/logs")  # insert log or batch
async def logs_set():
    return {}
@app.delete("/api/v1/logs") # del based on application and date range
async def logs_del():
    return {}
@app.delete("/api/v1/logs/all") # clear all logs
async def logs_del_all():
    return {}

@app.get("/api/v1/counters") # counter, app_name optional
async def cpunters_get():
    return {}
