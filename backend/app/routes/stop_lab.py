from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from kuberange_common.models import LabSession
from kuberange_common.kubernetes_service import delete_lab_pod

router = APIRouter()

@router.delete("/stop/{session_id}")
def stop_lab(session_id: int, db: Session = Depends(get_db)):

    # look up the lab session in the database
    lab_session = db.query(LabSession).filter(LabSession.id == session_id).first()
    if not lab_session:
        raise HTTPException(status_code=404, detail="Lab session not found")

    # tell kubernetes to delete the pod (404 = already gone, treated as success)
    try:
        delete_lab_pod(lab_session.pod_name)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    lab_session.status = "stopped"
    try:
        db.commit()
    except Exception:
        db.rollback()
        # pod is already deleted — surface this so the caller knows state is inconsistent
        raise HTTPException(
            status_code=500,
            detail="Pod was deleted but failed to update session status; retry to re-sync"
        )

    return {"message": "Lab stopped", "session_id": session_id}
