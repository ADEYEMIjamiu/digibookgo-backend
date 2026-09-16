from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)

class MapNode(Base):
    __tablename__ = "map_nodes"
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    x = Column(Float)
    y = Column(Float)
    floor = Column(Integer, default=0)
    label = Column(String, nullable=True)

class MapEdge(Base):
    __tablename__ = "map_edges"
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    node_a_id = Column(Integer, ForeignKey("map_nodes.id"))
    node_b_id = Column(Integer, ForeignKey("map_nodes.id"))
    distance = Column(Float)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    barcode = Column(String, nullable=True)

class ProductLocation(Base):
    __tablename__ = "product_locations"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    store_id = Column(Integer, ForeignKey("stores.id"))
    nearest_node_id = Column(Integer, ForeignKey("map_nodes.id"))
    shelf_label = Column(String, nullable=True)


class Marker(Base):
    __tablename__ = "markers"
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    node_id = Column(Integer, ForeignKey("map_nodes.id"))
    code = Column(String, unique=True)
