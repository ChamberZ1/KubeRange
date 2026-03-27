from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import start_lab, stop_lab, status, lab_types, active_session

app = FastAPI(title="KubeRange API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(start_lab.router)
app.include_router(stop_lab.router)
app.include_router(status.router)
app.include_router(lab_types.router)
app.include_router(active_session.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}