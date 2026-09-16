from pydantic import BaseModel
from typing import Optional

class StoreCreate(BaseModel):
    name: str
    city: str

class StoreOut(BaseModel):
    id: int
    name: str
    city: str

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    barcode: Optional[str] = None

class ProductOut(BaseModel):
    id: int
    name: str
    barcode: Optional[str] = None

    class Config:
        from_attributes = True

class ProductLocationCreate(BaseModel):
    product_id: int
    store_id: int
    nearest_node_id: int
    shelf_label: Optional[str] = None

class ProductLocationOut(BaseModel):
    id: int
    product_id: int
    store_id: int
    nearest_node_id: int
    shelf_label: Optional[str] = None

    class Config:
        from_attributes = True


class MarkerCreate(BaseModel):
    store_id: int
    node_id: int
    code: str

class MarkerOut(BaseModel):
    id: int
    store_id: int
    node_id: int
    code: str

    class Config:
        from_attributes = True
