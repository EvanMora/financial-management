from fastapi.testclient import TestClient
from app.main import app

# Creamos el cliente de pruebas basado en nuestra aplicación de FastAPI
client = TestClient(app)

def test_read_home():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {"mensaje": "Hola gestion finanzas"}
