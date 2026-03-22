from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="KubeRange API")

DATABASE_URL = os.getenv("DATABASE_URL")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}