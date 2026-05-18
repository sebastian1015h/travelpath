"""
Tests de integración — requieren la app corriendo con DB de prueba.
Ejecutar con: pytest tests/integration/ -v
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.application.dtos.aeropuerto_dto import AeropuertoDTO


def _futuro(horas=24):
    return (datetime.utcnow() + timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M:%S")


@pytest.fixture
def app():
    with patch("src.infrastructure.config.database.create_engine"), \
         patch("src.infrastructure.config.database.init_db"), \
         patch("src.infrastructure.adapters.output.external.api_colombia_adapter.ApiColombiaAdapter") as MockAdapter:

        mock_client = MagicMock()
        mock_client.buscar_por_iata.return_value = AeropuertoDTO(
            iata="BOG", nombre="El Dorado", ciudad="Bogotá", pais="Colombia", latitud=4.7, longitud=-74.1
        )
        MockAdapter.return_value = mock_client

        from src.infrastructure.config.dependencies import create_app as _create_app
        application = _create_app()
        application.config["TESTING"] = True
        application.config["JWT_SECRET_KEY"] = "test-secret"
        yield application


@pytest.fixture
def client(app):
    return app.test_client()


def _registrar_y_login(client, correo="test@test.com"):
    client.post("/auth/register", json={"nombre": "Test", "correo": correo, "contrasena": "password123"})
    res = client.post("/auth/login", json={"correo": correo, "contrasena": "password123"})
    if res.status_code == 200:
        return res.get_json()["access_token"]
    return None


def test_register_endpoint(client):
    res = client.post("/auth/register", json={
        "nombre": "Juan", "correo": "juan@test.com", "contrasena": "password123"
    })
    assert res.status_code in (201, 409)


def test_login_con_credenciales_invalidas(client):
    res = client.post("/auth/login", json={"correo": "noexiste@test.com", "contrasena": "wrong"})
    assert res.status_code == 401


def test_listar_sin_token_retorna_401(client):
    res = client.get("/api/itinerarios")
    assert res.status_code == 401


def test_buscar_aeropuerto_sin_token(client):
    res = client.get("/api/aeropuertos?nombre=bog")
    assert res.status_code == 401
