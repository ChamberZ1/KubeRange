from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from kuberange_common.models import LabType

router = APIRouter()

@router.get("/lab-types")
def get_lab_types(db: Session = Depends(get_db)):
    return db.query(LabType).all()
