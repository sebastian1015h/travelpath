from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Aeropuerto:
    iata_code: str
    nombre: str
    ciudad: str
    pais: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    def __post_init__(self):
        if len(self.iata_code) != 3:
            raise ValueError(f"Código IATA inválido: {self.iata_code}")
