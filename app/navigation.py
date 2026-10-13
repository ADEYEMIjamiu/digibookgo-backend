from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from .pathfinding import build_graph, shortest_path

router = APIRouter(prefix="/api/navigation", tags=["navigation"])

# The visual demo page is also served at /api/navigation/demo, because the
# live server only forwards /api/... paths to the backend. If demo.py is
# missing or broken, the rest of the API keeps working.
try:
    from .demo import router as demo_router
    router.include_router(demo_router)
except Exception:
    pass


def _fmt(n):
    return str(int(n)) if float(n).is_integer() else f"{n:.1f}"


def build_steps(path, node_map, labels, edge_len, product_name, shelf_label):
    """Turn a node path into simple walking directions.

    Actions: walk, turn_left, turn_right, turn_around, arrive.
    Left/right is relative to a map drawn like a screen: x to the right,
    y pointing down.
    """
    segments = []
    for a, b in zip(path, path[1:]):
        dx = node_map[b]["x"] - node_map[a]["x"]
        dy = node_map[b]["y"] - node_map[a]["y"]
        length = edge_len.get((min(a, b), max(a, b)), (dx * dx + dy * dy) ** 0.5)
        segments.append({"dx": dx, "dy": dy, "length": length, "to": b})

    # Merge consecutive segments that continue in the same straight direction
    merged = []
    for seg in segments:
        last = merged[-1] if merged else None
        if (
            last
            and abs(last["dx"] * seg["dy"] - last["dy"] * seg["dx"]) < 1e-9
            and last["dx"] * seg["dx"] + last["dy"] * seg["dy"] > 0
        ):
            last["length"] += seg["length"]
            last["to"] = seg["to"]
            last["dx"] += seg["dx"]
            last["dy"] += seg["dy"]
        else:
            merged.append(dict(seg))

    steps = []
    for i, seg in enumerate(merged):
        place = labels.get(seg["to"], f"node {seg['to']}")
        dist = _fmt(seg["length"])
        if i == 0:
            action, text = "walk", f"Walk {dist} m to {place}"
        else:
            prev = merged[i - 1]
            cross = prev["dx"] * seg["dy"] - prev["dy"] * seg["dx"]
            dot = prev["dx"] * seg["dx"] + prev["dy"] * seg["dy"]
            if abs(cross) < 1e-9 and dot < 0:
                action, text = "turn_around", f"Turn around, walk {dist} m to {place}"
            elif cross > 0:
                action, text = "turn_right", f"Turn right, walk {dist} m to {place}"
            else:
                action, text = "turn_left", f"Turn left, walk {dist} m to {place}"
        steps.append({
            "action": action,
            "distance": round(seg["length"], 1),
            "to_node_id": seg["to"],
            "to_label": place,
            "text": text,
        })

    where = shelf_label or "the marked shelf"
    steps.append({
        "action": "arrive",
        "distance": 0,
        "to_node_id": path[-1],
        "to_label": labels.get(path[-1], f"node {path[-1]}"),
        "text": f"Arrive: {product_name} is at {where}",
    })
    return steps


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
    labels = {n.id: (n.label or f"node {n.id}") for n in nodes}
    edge_len = {
        (min(e.node_a_id, e.node_b_id), max(e.node_a_id, e.node_b_id)): e.distance
        for e in edges
    }
    product = db.query(models.Product).filter_by(id=to_product_id).first()
    product_name = product.name if product else "Product"

    return {
        "path_node_ids": path,
        "coordinates": [node_map[nid] for nid in path],
        "distance": distance,
        "shelf_label": location.shelf_label,
        "steps": build_steps(path, node_map, labels, edge_len, product_name, location.shelf_label),
    }
