from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from src.application.dtos.aeropuerto_dto import AeropuertoDTO


@dataclass
class CrearItinerarioDTO:
    aeropuerto_origen_iata: str
    aeropuerto_destino_iata: str
    fecha_hora_salida: datetime
    fecha_hora_llegada: datetime
    notas: str = ""


@dataclass
class ModificarItinerarioDTO:
    aeropuerto_origen_iata: Optional[str] = None
    aeropuerto_destino_iata: Optional[str] = None
    fecha_hora_salida: Optional[datetime] = None
    fecha_hora_llegada: Optional[datetime] = None
    notas: Optional[str] = None


@dataclass
class ItinerarioResponseDTO:
    id: str
    usuario_id: str
    aeropuerto_origen: AeropuertoDTO
    aeropuerto_destino: AeropuertoDTO
    fecha_hora_salida: datetime
    fecha_hora_llegada: datetime
    duracion_minutos: int
    notas: str
    activo: bool
    created_at: datetime

    def duracion_formateada(self) -> str:
        horas = self.duracion_minutos // 60
        minutos = self.duracion_minutos % 60
        return f"{horas}h {minutos}m"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "aeropuerto_origen": self.aeropuerto_origen.to_dict(),
            "aeropuerto_destino": self.aeropuerto_destino.to_dict(),
            "fecha_hora_salida": self.fecha_hora_salida.isoformat(),
            "fecha_hora_llegada": self.fecha_hora_llegada.isoformat(),
            "duracion_minutos": self.duracion_minutos,
            "duracion_formateada": self.duracion_formateada(),
            "notas": self.notas,
            "activo": self.activo,
            "created_at": self.created_at.isoformat(),
        }
