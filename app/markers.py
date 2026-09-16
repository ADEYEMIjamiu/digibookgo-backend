from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/markers", tags=["markers"])

@router.post("/", response_model=schemas.MarkerOut)
def create_marker(marker: schemas.MarkerCreate, db: Session = Depends(get_db)):
    new_marker = models.Marker(
        store_id=marker.store_id,
        node_id=marker.node_id,
        code=marker.code
    )
    db.add(new_marker)
    db.commit()
    db.refresh(new_marker)
    return new_marker

@router.get("/", response_model=list[schemas.MarkerOut])
def list_markers(db: Session = Depends(get_db)):
    return db.query(models.Marker).all()

@router.get("/scan/{code}", response_model=schemas.MarkerOut)
def scan_marker(code: str, db: Session = Depends(get_db)):
    marker = db.query(models.Marker).filter(models.Marker.code == code).first()
    if not marker:
        raise HTTPException(status_code=404, detail="Marker not found")
    return marker
