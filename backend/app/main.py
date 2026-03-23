from fastapi import FastAPI
from app.routes import start_lab, stop_lab, status

app = FastAPI(title="KubeRange API")

app.include_router(start_lab.router)
app.include_router(stop_lab.router)
app.include_router(status.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}