from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from kuberange_common.models import LabSession
from app.db.schemas import LabSessionResponse

router = APIRouter()

@router.get("/status/{session_id}", response_model=LabSessionResponse)
def get_lab_status(session_id: int, db: Session = Depends(get_db)):

    lab_session = db.get(LabSession, session_id)
    if not lab_session:
        raise HTTPException(status_code=404, detail="Lab session not found")

    return lab_session