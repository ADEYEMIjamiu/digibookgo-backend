#!/usr/bin/env python3
"""
Seed a demo store into the digibookgo API and test the routes.

Usage:
    python3 seed_demo_store.py                             # local server (127.0.0.1:8001)
    python3 seed_demo_store.py https://go.digibook.cloud   # live server

Uses only the Python standard library, so nothing needs to be installed.
Safe to re-run: it stops if "Lidl Demo Store" already exists.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001").rstrip("/")

STORE = {"name": "Lidl Demo Store", "city": "Berlin"}

# key, label, x, y   (metres, floor 0)
NODES = [
    ("entrance", "Entrance",            0,  0),
    ("produce",  "Fruit & Vegetables",  6,  0),
    ("bakery",   "Bakery",             12,  0),
    ("dairy",    "Dairy",              18,  0),
    ("aisle1",   "Aisle 1",             6,  8),
    ("aisle2",   "Aisle 2",            12,  8),
    ("frozen",   "Frozen Foods",       18,  8),
    ("snacks",   "Snacks & Sweets",     6, 16),
    ("drinks",   "Drinks",             12, 16),
    ("checkout", "Checkout",           18, 16),
]

# node_a, node_b, walking distance in metres
# node_a is always the node closer to the entrance, so the routes work
# whether the pathfinding treats edges as one-way or two-way.
EDGES = [
    ("entrance", "produce",  6),
    ("produce",  "bakery",   6),
    ("bakery",   "dairy",    6),
    ("produce",  "aisle1",   8),
    ("bakery",   "aisle2",   8),
    ("dairy",    "frozen",   8),
    ("aisle1",   "aisle2",   7),
    ("aisle2",   "frozen",   7),
    ("aisle1",   "snacks",   8),
    ("aisle2",   "drinks",   8),
    ("frozen",   "checkout", 8),
    ("snacks",   "drinks",   7),
    ("drinks",   "checkout", 7),
]

# name, barcode, node key, shelf label
PRODUCTS = [
    ("Paprika Chips", "4000000000011", "snacks",  "Shelf B3"),
    ("Milk Chocolate", "4000000000028", "snacks",  "Shelf B1"),
    ("Orange Juice",  "4000000000035", "drinks",  "Shelf D2"),
    ("Mineral Water", "4000000000042", "drinks",  "Shelf D1"),
    ("Fresh Bread",   "4000000000059", "bakery",  "Shelf A2"),
    ("Whole Milk",    "4000000000066", "dairy",   "Shelf C1"),
    ("Frozen Pizza",  "4000000000073", "frozen",  "Freezer F4"),
    ("Apples",        "4000000000080", "produce", "Shelf P1"),
]

# QR code text, node key
MARKERS = [
    ("LIDL-DEMO-ENTRANCE", "entrance"),
    ("LIDL-DEMO-AISLE-1",  "aisle1"),
    ("LIDL-DEMO-DRINKS",   "drinks"),
]


def call(method, path, body=None, fatal=True):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        msg = f"  ERROR {e.code} on {method} {path}\n  {e.read().decode()}"
        if fatal:
            print("\n" + msg)
            sys.exit(1)
        print(msg)
        return None
    except urllib.error.URLError as e:
        print(f"\nCannot reach {BASE}: {e.reason}")
        sys.exit(1)


def main():
    print(f"Target server: {BASE}\n")

    # Safety check: do not create the demo store twice
    for s in call("GET", "/api/stores/"):
        if s["name"] == STORE["name"]:
            print(f"'{STORE['name']}' already exists (store id {s['id']}). Nothing to do.")
            print("Delete it first if you want to rebuild it.")
            return

    store = call("POST", "/api/stores/", STORE)
    store_id = store["id"]
    print(f"Store created: {store['name']} (id {store_id})")

    # Nodes
    node_ids = {}
    for key, label, x, y in NODES:
        n = call("POST", "/api/map/nodes",
                 {"store_id": store_id, "x": x, "y": y, "floor": 0, "label": label})
        node_ids[key] = n["id"]
    print(f"Nodes created: {len(node_ids)}")
    id_to_label = {node_ids[k]: label for k, label, _, _ in NODES}

    # Edges
    for a, b, dist in EDGES:
        call("POST", "/api/map/edges",
             {"store_id": store_id, "node_a_id": node_ids[a],
              "node_b_id": node_ids[b], "distance": dist})
    print(f"Edges created: {len(EDGES)}")

    # Products and their shelf locations
    product_ids = {}
    for name, barcode, node_key, shelf in PRODUCTS:
        p = call("POST", "/api/products/", {"name": name, "barcode": barcode})
        product_ids[name] = p["id"]
        call("POST", "/api/products/locations",
             {"product_id": p["id"], "store_id": store_id,
              "nearest_node_id": node_ids[node_key], "shelf_label": shelf})
    print(f"Products placed on shelves: {len(PRODUCTS)}")

    # QR markers
    for code, node_key in MARKERS:
        call("POST", "/api/markers/",
             {"store_id": store_id, "node_id": node_ids[node_key], "code": code})
    print(f"QR markers created: {len(MARKERS)}")

    # ---- Tests ----
    print("\n=== ROUTE TESTS (from Entrance) ===")
    start = node_ids["entrance"]
    failures = 0
    for name, _, _, _ in PRODUCTS:
        r = call("GET",
                 f"/api/navigation/route?store_id={store_id}&from_node={start}"
                 f"&to_product_id={product_ids[name]}", fatal=False)
        if r is None:
            failures += 1
            continue
        path = " -> ".join(id_to_label[i] for i in r["path_node_ids"])
        print(f"  {name:15} {path}  ({r['distance']} m)  [{r['shelf_label']}]")

    print("\n=== ROUTE TEST (start from Aisle 1 QR marker, reverse direction) ===")
    r = call("GET",
             f"/api/navigation/route?store_id={store_id}&from_node={node_ids['aisle1']}"
             f"&to_product_id={product_ids['Fresh Bread']}", fatal=False)
    if r is None:
        failures += 1
        print("  Failed: edges may be one-way. Tell Claude and the reverse edges will be added.")
    else:
        path = " -> ".join(id_to_label[i] for i in r["path_node_ids"])
        print(f"  Fresh Bread     {path}  ({r['distance']} m)  [{r['shelf_label']}]")

    print("\n=== QR SCAN TEST ===")
    scan = call("GET", f"/api/markers/scan/{MARKERS[0][0]}", fatal=False)
    print(f"  {MARKERS[0][0]} -> {scan}")

    print("\n" + ("ALL TESTS PASSED" if failures == 0 else f"{failures} TEST(S) FAILED"))
    print(f"\nDemo store id: {store_id}   Entrance node id: {node_ids['entrance']}")
    print("Product ids:", ", ".join(f"{n}={i}" for n, i in product_ids.items()))


if __name__ == "__main__":
    main()
