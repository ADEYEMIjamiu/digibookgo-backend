from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from .pathfinding import build_graph, shortest_path

router = APIRouter(prefix="/api/navigation", tags=["navigation"])

@router.get("/route")
def get_route(store_id: int, from_node: int, to_product_id: int, db: Session = Depends(get_db)):
    location = db.query(models.ProductLocation).filter_by(
        store_id=store_id, product_id=to_product_id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Product not found in this store")

    edges = db.query(models.MapEdge).filter_by(store_id=store_id).all()
    graph = build_graph(edges)
    path, distance = shortest_path(graph, from_node, location.nearest_node_id)

    if path is None:
        raise HTTPException(status_code=404, detail="No path found")

    nodes = db.query(models.MapNode).filter(models.MapNode.id.in_(path)).all()
    node_map = {n.id: {"x": n.x, "y": n.y, "floor": n.floor} for n in nodes}

    return {
        "path_node_ids": path,
        "coordinates": [node_map[nid] for nid in path],
        "distance": distance,
        "shelf_label": location.shelf_label
    }
