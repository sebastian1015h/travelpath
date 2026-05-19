from abc import ABC, abstractmethod
from typing import List, Optional
from src.application.dtos.aeropuerto_dto import AeropuertoDTO


class AeropuertoClientPort(ABC):

    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> List[AeropuertoDTO]: ...

    @abstractmethod
    def buscar_por_iata(self, iata: str) -> Optional[AeropuertoDTO]: ...

    @abstractmethod
    def listar_aeropuertos(self, pagina: int = 1) -> List[AeropuertoDTO]: ...
