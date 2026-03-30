from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import start_lab, stop_lab, status, lab_types, active_session

app = FastAPI(title="KubeRange API")

# Cross-Origin resource sharing (CORS) - a browser security rule: If frontend is on localhost:5173
# and tries to call localhost:8000, the browser blocks it because the ports are different.
# The server must explicitly say "I allow requests from that origin" via CORS headers.

# Middleware is code that runs on every request before it hits the route handlers
# This call function call tells FastAPI to attach CORS headers to every response automatically.
# Keeping this functionality here for local dev convenience.
# In production, CORS between browser and backend is not triggered due to NGINX making all requests come from the same origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # If care about security in production, tighten this.
    allow_methods=["*"],
    allow_headers=["*"],
)

# Let's FastAPI know about the API routes in separate files.
app.include_router(start_lab.router)
app.include_router(stop_lab.router)
app.include_router(status.router)
app.include_router(lab_types.router)
app.include_router(active_session.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}