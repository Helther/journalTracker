from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def root():
    return {}

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
