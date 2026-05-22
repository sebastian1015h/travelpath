from dataclasses import dataclass
from typing import Optional


@dataclass
class AeropuertoDTO:
    iata: str
    nombre: str
    ciudad: str
    pais: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "iata": self.iata,
            "nombre": self.nombre,
            "ciudad": self.ciudad,
            "pais": self.pais,
            "latitud": self.latitud,
            "longitud": self.longitud,
        }
