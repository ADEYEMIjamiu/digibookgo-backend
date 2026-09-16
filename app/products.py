from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/products", tags=["products"])

@router.post("/", response_model=schemas.ProductOut)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    new_product = models.Product(name=product.name, barcode=product.barcode)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/", response_model=list[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@router.post("/locations", response_model=schemas.ProductLocationOut)
def create_product_location(location: schemas.ProductLocationCreate, db: Session = Depends(get_db)):
    new_location = models.ProductLocation(
        product_id=location.product_id,
        store_id=location.store_id,
        nearest_node_id=location.nearest_node_id,
        shelf_label=location.shelf_label
    )
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location

@router.get("/locations", response_model=list[schemas.ProductLocationOut])
def list_product_locations(db: Session = Depends(get_db)):
    return db.query(models.ProductLocation).all()
