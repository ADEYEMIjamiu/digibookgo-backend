from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/stores", tags=["stores"])

@router.post("/", response_model=schemas.StoreOut)
def create_store(store: schemas.StoreCreate, db: Session = Depends(get_db)):
    new_store = models.Store(name=store.name, city=store.city)
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    return new_store

@router.get("/", response_model=list[schemas.StoreOut])
def list_stores(db: Session = Depends(get_db)):
    return db.query(models.Store).all()
