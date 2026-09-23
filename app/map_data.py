from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/map", tags=["map"])

@router.post("/nodes", response_model=schemas.MapNodeOut)
def create_node(node: schemas.MapNodeCreate, db: Session = Depends(get_db)):
    new_node = models.MapNode(
        store_id=node.store_id,
        x=node.x,
        y=node.y,
        floor=node.floor,
        label=node.label
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node

@router.get("/nodes", response_model=list[schemas.MapNodeOut])
def list_nodes(store_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.MapNode)
    if store_id is not None:
        query = query.filter(models.MapNode.store_id == store_id)
    return query.all()

@router.post("/edges", response_model=schemas.MapEdgeOut)
def create_edge(edge: schemas.MapEdgeCreate, db: Session = Depends(get_db)):
    new_edge = models.MapEdge(
        store_id=edge.store_id,
        node_a_id=edge.node_a_id,
        node_b_id=edge.node_b_id,
        distance=edge.distance
    )
    db.add(new_edge)
    db.commit()
    db.refresh(new_edge)
    return new_edge

@router.get("/edges", response_model=list[schemas.MapEdgeOut])
def list_edges(store_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.MapEdge)
    if store_id is not None:
        query = query.filter(models.MapEdge.store_id == store_id)
    return query.all()
