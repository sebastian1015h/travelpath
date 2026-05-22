"""
Tests de integración con SQLite en memoria.
Ejecutar con: pytest tests/integration/ -v
"""
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-chars-minimum!")
os.environ.setdefault("FLASK_DEBUG", "False")


@pytest.fixture(scope="module")
def app():
    from src.infrastructure.config.dependencies import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def _registrar_y_login(client, correo="test@test.com"):
    client.post("/auth/register", json={
        "nombre": "Test", "correo": correo, "contrasena": "password123"
    })
    res = client.post("/auth/login", json={"correo": correo, "contrasena": "password123"})
    if res.status_code == 200:
        return res.get_json()["access_token"]
    return None


def test_register_endpoint(client):
    res = client.post("/auth/register", json={
        "nombre": "Juan", "correo": "juan@integration.com", "contrasena": "password123"
    })
    assert res.status_code in (201, 409)


def test_login_con_credenciales_invalidas(client):
    res = client.post("/auth/login", json={
        "correo": "noexiste@test.com", "contrasena": "wrong"
    })
    assert res.status_code == 401


def test_listar_sin_token_retorna_401(client):
    res = client.get("/api/itinerarios")
    assert res.status_code == 401


def test_buscar_aeropuerto_sin_token(client):
    res = client.get("/api/aeropuertos?nombre=bog")
    assert res.status_code == 401


def test_login_exitoso_devuelve_token(client):
    client.post("/auth/register", json={
        "nombre": "Ana", "correo": "ana@integration.com", "contrasena": "secret123"
    })
    res = client.post("/auth/login", json={
        "correo": "ana@integration.com", "contrasena": "secret123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data


def test_listar_con_token_retorna_200(client):
    token = _registrar_y_login(client, "lista@integration.com")
    assert token is not None
    res = client.get("/api/itinerarios", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
