from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import ia as api_ia
from app.api import movimientos as api_movimientos
from app.web import views

# Variables del archivo .env (p. ej. GEMINI_API_KEY). Las que ya existan en el entorno no se pisan.
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(views.router)
app.include_router(api_movimientos.router)
app.include_router(api_ia.router)

@app.get("/")
def home():
    return {"mensaje": "Hola bibliopedia"}
