import pytest
from datetime import datetime, timedelta

from src.domain.entities.itinerario import Itinerario
from src.domain.exceptions.domain_exceptions import (
    FechaInvalidaException,
    OrigenIgualDestinoException,
)


def _futuro(horas=2):
    return datetime.utcnow() + timedelta(hours=horas)


def _pasado(horas=2):
    return datetime.utcnow() - timedelta(hours=horas)


def _itinerario(**kwargs):
    defaults = dict(
        usuario_id="user-1",
        aeropuerto_origen_iata="BOG",
        aeropuerto_destino_iata="MDE",
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(3),
    )
    defaults.update(kwargs)
    return Itinerario(**defaults)


def test_crea_itinerario_valido():
    it = _itinerario()
    assert it.aeropuerto_origen_iata == "BOG"
    assert it.activo is True


def test_permite_vuelo_en_el_pasado():
    it = _itinerario(
        fecha_hora_salida=_pasado(5),
        fecha_hora_llegada=_pasado(3),
    )
    assert it.activo is True


def test_permite_vuelo_hoy():
    it = _itinerario(
        fecha_hora_salida=_pasado(1),
        fecha_hora_llegada=_futuro(1),
    )
    assert it.activo is True


def test_no_permite_llegada_antes_de_salida():
    with pytest.raises(FechaInvalidaException):
        _itinerario(
            fecha_hora_salida=_futuro(3),
            fecha_hora_llegada=_futuro(2),
        )


def test_origen_igual_destino_lanza_excepcion():
    with pytest.raises(OrigenIgualDestinoException):
        _itinerario(aeropuerto_origen_iata="BOG", aeropuerto_destino_iata="BOG")


def test_calcula_duracion_correctamente():
    it = _itinerario(
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(4),
    )
    assert it.calcular_duracion() == 120


def test_es_pasado_retorna_false_para_futuro():
    it = _itinerario()
    assert it.es_pasado() is False


def test_es_pasado_retorna_true_para_pasado():
    it = object.__new__(Itinerario)
    it.fecha_hora_salida = datetime.utcnow() - timedelta(hours=1)
    assert it.es_pasado() is True


def test_borrado_logico():
    it = _itinerario()
    it.desactivar()
    assert it.activo is False


def test_duracion_fraccionada():
    it = _itinerario(
        fecha_hora_salida=_futuro(2),
        fecha_hora_llegada=_futuro(2) + timedelta(minutes=90),
    )
    assert it.calcular_duracion() == 90
