from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from src.domain.exceptions.domain_exceptions import (
    FechaInvalidaException,
    OrigenIgualDestinoException,
)


@dataclass
class Itinerario:
    usuario_id: str
    aeropuerto_origen_iata: str
    aeropuerto_destino_iata: str
    fecha_hora_salida: datetime
    fecha_hora_llegada: datetime
    notas: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self._validar()

    def _validar(self):
        self.validar_fechas()
        self.validar_origen_distinto()

    def validar_fechas(self):
        if self.fecha_hora_llegada <= self.fecha_hora_salida:
            raise FechaInvalidaException("La llegada debe ser posterior a la salida.")

    def validar_origen_distinto(self):
        if self.aeropuerto_origen_iata.upper() == self.aeropuerto_destino_iata.upper():
            raise OrigenIgualDestinoException(
                "El origen y el destino no pueden ser el mismo aeropuerto."
            )

    def calcular_duracion(self) -> int:
        """Retorna la duración del viaje en minutos."""
        delta = self.fecha_hora_llegada - self.fecha_hora_salida
        return int(delta.total_seconds() / 60)

    def es_pasado(self) -> bool:
        return self.fecha_hora_salida < datetime.utcnow()

    def desactivar(self):
        """Borrado lógico."""
        self.activo = False
        self.updated_at = datetime.utcnow()
