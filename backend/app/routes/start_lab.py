from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.database import get_db
from kuberange_common.models import LabType, LabSession
from app.db.schemas import LabSessionResponse
from kuberange_common.kubernetes_service import create_lab_pod
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/start/{lab_type_id}", response_model=LabSessionResponse)
def start_lab(lab_type_id: int, db: Session = Depends(get_db)):

    # lazily expire any session the worker hasn't cleaned up yet,
    # so the unique index doesn't block a new start after expiry
    expired = db.query(LabSession).filter(
        LabSession.status == "running",
        LabSession.expiration_time <= datetime.now(timezone.utc).replace(tzinfo=None)
    ).first()
    if expired:
        expired.status = "expired"
        db.commit()

    # look up the lab type in the database
    lab_type = db.query(LabType).filter(LabType.id == lab_type_id).first()
    if not lab_type:
        raise HTTPException(status_code=404, detail="Lab type not found")

    # insert the session row first — pod_name/url filled in after pod creation.
    # the partial unique index (WHERE status = 'running') means only one running
    # row can exist. if a concurrent request already inserted one, the commit
    # below raises IntegrityError and we return 409 without touching Kubernetes.
    lab_session = LabSession(
        lab_type_id=lab_type_id,
        status="running",
        start_time=datetime.now(timezone.utc).replace(tzinfo=None),
        expiration_time=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
    )
    db.add(lab_session)
    try:
        db.commit()  # SQLAlchemy tells Postgres to execute the lab_session insert. This is where postgres checks the unique index.
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A lab is already running. Please stop it before starting a new one.")

    # now create the pod
    try:
        pod_name, url = create_lab_pod(lab_type.name, lab_type.image, lab_type.port)
    except RuntimeError as e:
        # pod creation failed — remove the session row so the slot is freed
        db.delete(lab_session)
        db.commit()
        raise HTTPException(status_code=503, detail=str(e))

    # update the row with the real pod details
    lab_session.pod_name = pod_name
    lab_session.url = url
    db.commit()
    db.refresh(lab_session)

    return lab_session
