from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from kuberange_common.models import LabType, LabSession
from app.db.schemas import LabSessionResponse
from kuberange_common.kubernetes_service import create_lab_pod, delete_lab_pod
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/start/{lab_type_id}", response_model=LabSessionResponse)  # pass the lab type as an URL param
def start_lab(lab_type_id: int, db: Session = Depends(get_db)):

    # look up the lab type in the database
    lab_type = db.query(LabType).filter(LabType.id == lab_type_id).first()
    if not lab_type:
        raise HTTPException(status_code=404, detail="Lab type not found")

    # tell kubernetes to spin up the pod
    try:
        pod_name, url = create_lab_pod(lab_type.name, lab_type.image, lab_type.port)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # store the session in the database
    lab_session = LabSession(
        lab_type_id=lab_type_id,
        pod_name=pod_name,
        url=url,
        status="running",
        start_time=datetime.now(),
        expiration_time=datetime.now() + timedelta(minutes=30)
    )
    db.add(lab_session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # pod was created but DB failed — attempt cleanup to avoid orphan
        try:
            delete_lab_pod(pod_name)
            detail = "Failed to save lab session; pod has been cleaned up"
        except RuntimeError:
            detail = f"Failed to save lab session; pod '{pod_name}' may need manual cleanup"
        raise HTTPException(status_code=500, detail=detail)
    db.refresh(lab_session)

    return lab_session
