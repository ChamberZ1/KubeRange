import time
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from kuberange_common.models import LabSession
from kuberange_common.kubernetes_service import delete_lab_pod

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Copy .env.example to .env and fill in your database credentials."
    )
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def cleanup_expired_labs():
    db = SessionLocal()
    try:
        expired_sessions = db.query(LabSession).filter(
            LabSession.status == "running",
            LabSession.expiration_time <= datetime.now()
        ).all()

        for session in expired_sessions:
            try:
                delete_lab_pod(session.pod_name)
                session.status = "expired"
                db.commit()
                print(f"Expired lab {session.pod_name} deleted")
            except Exception as e:
                db.rollback()  # if pod deletion fails, we don't want to mark the session as expired in the DB
                print(f"Failed to delete pod {session.pod_name}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Cleanup worker started")
    while True:
        cleanup_expired_labs()
        time.sleep(60)