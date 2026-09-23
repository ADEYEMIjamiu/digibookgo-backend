from fastapi import FastAPI
from datetime import date
from .database import engine, Base
from . import models, stores, products, markers, navigation, map_data

Base.metadata.create_all(bind=engine)

app = FastAPI(title="digibookgo API")

app.include_router(stores.router)
app.include_router(products.router)
app.include_router(markers.router)
app.include_router(navigation.router)
app.include_router(map_data.router)

@app.get("/api/health")
def health():
    return {
        "project": "digibookgo",
        "status": "ok",
        "port": 3957,
        "name": "Ade"
    }


@app.get("/api/date")
def get_date():
    return {"today": str(date.today())}
