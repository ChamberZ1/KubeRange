from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from app.db.database import get_db
from kuberange_common.models import LabSession
from app.db.schemas import LabSessionResponse

router = APIRouter()

@router.get("/session/active", response_model=Optional[LabSessionResponse])
def get_active_session(db: Session = Depends(get_db)):
    session = db.query(LabSession).filter(LabSession.status == "running").first()
    if session is None:
        return None
    # lazily expire sessions the worker hasn't cleaned up yet
    if session.expiration_time and session.expiration_time <= datetime.now(timezone.utc).replace(tzinfo=None):
        session.status = "expired"
        db.commit()
        return None
    return session
