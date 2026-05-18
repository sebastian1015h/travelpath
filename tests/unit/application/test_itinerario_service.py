import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.application.services.itinerario_service import ItinerarioService
from src.application.dtos.itinerario_dto import CrearItinerarioDTO
from src.application.dtos.aeropuerto_dto import AeropuertoDTO
from src.domain.exceptions.domain_exceptions import (
    SuperposicionDeViajesException,
    AeropuertoNoEncontradoException,
    ItinerarioNoEncontradoException,
)


def _futuro(horas=2):
    return datetime.utcnow() + timedelta(hours=horas)


def _aeropuerto(iata="BOG"):
    return AeropuertoDTO(iata=iata, nombre=f"Aeropuerto {iata}", ciudad="Ciudad", pais="Colombia", latitud=4.0, longitud=-74.0)


@pytest.fixture
def servicio():
    repo = MagicMock()
    client = MagicMock()
    return ItinerarioService(repo, client), repo, client


def test_crear_itinerario_exitoso(servicio):
    svc, repo, client = servicio
    client.buscar_por_iata.side_effect = [_aeropuerto("BOG"), _aeropuerto("MDE")]
    repo.existe_superposicion.return_value = False

    from src.domain.entities.itinerario import Itinerario
    it = Itinerario(
        usuario_id="u1",
        aeropuerto_origen_iata="BOG",
        aeropuerto_destino_iata="MDE",
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(4),
    )
    repo.guardar.return_value = it

    dto = CrearItinerarioDTO(
        aeropuerto_origen_iata="BOG",
        aeropuerto_destino_iata="MDE",
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(4),
    )
    resultado = svc.crear(dto, "u1")
    assert resultado.aeropuerto_origen.iata == "BOG"
    repo.guardar.assert_called_once()


def test_detecta_superposicion(servicio):
    svc, repo, client = servicio
    client.buscar_por_iata.side_effect = [_aeropuerto("BOG"), _aeropuerto("MDE")]
    repo.existe_superposicion.return_value = True

    dto = CrearItinerarioDTO(
        aeropuerto_origen_iata="BOG",
        aeropuerto_destino_iata="MDE",
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(4),
    )
    with pytest.raises(SuperposicionDeViajesException):
        svc.crear(dto, "u1")


def test_aeropuerto_no_encontrado_lanza_excepcion(servicio):
    svc, repo, client = servicio
    client.buscar_por_iata.return_value = None

    dto = CrearItinerarioDTO(
        aeropuerto_origen_iata="XXX",
        aeropuerto_destino_iata="MDE",
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(4),
    )
    with pytest.raises(AeropuertoNoEncontradoException):
        svc.crear(dto, "u1")


def test_eliminar_itinerario_no_encontrado(servicio):
    svc, repo, client = servicio
    repo.obtener_por_id.return_value = None
    with pytest.raises(ItinerarioNoEncontradoException):
        svc.eliminar("no-existe", "u1")


def test_listar_retorna_lista_vacia(servicio):
    svc, repo, client = servicio
    repo.listar_por_usuario.return_value = []
    resultado = svc.listar_por_usuario("u1")
    assert resultado == []
