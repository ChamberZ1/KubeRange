from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.main import get_db
from app.db.models import LabSession
from app.db.schemas import LabSessionResponse
from app.services.kubernetes_service import delete_lab_pod

router = APIRouter()

@router.delete("/stop/{session_id}")
def stop_lab(session_id: int, db: Session = Depends(get_db)):

    # look up the lab session in the database
    lab_session = db.query(LabSession).filter(LabSession.id == session_id).first()
    if not lab_session:
        raise HTTPException(status_code=404, detail="Lab session not found")

    # tell kubernetes to delete the pod
    delete_lab_pod(lab_session.pod_name)

    lab_session.status = "stopped"
    db.commit()

    return {"message": "Lab stopped", "session_id": session_id}