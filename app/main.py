from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import movimientos as api_movimientos
from app.web import views

app = FastAPI()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(views.router)
app.include_router(api_movimientos.router)

@app.get("/")
def home():
    return {"mensaje": "Hola bibliopedia"}
