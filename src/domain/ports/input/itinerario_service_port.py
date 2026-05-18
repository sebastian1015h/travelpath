from abc import ABC, abstractmethod
from typing import List
from src.application.dtos.itinerario_dto import (
    CrearItinerarioDTO,
    ModificarItinerarioDTO,
    ItinerarioResponseDTO,
)


class ItinerarioServicePort(ABC):

    @abstractmethod
    def crear(self, dto: CrearItinerarioDTO, usuario_id: str) -> ItinerarioResponseDTO: ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str) -> List[ItinerarioResponseDTO]: ...

    @abstractmethod
    def obtener_detalle(self, id: str, usuario_id: str) -> ItinerarioResponseDTO: ...

    @abstractmethod
    def modificar(self, id: str, dto: ModificarItinerarioDTO, usuario_id: str) -> ItinerarioResponseDTO: ...

    @abstractmethod
    def eliminar(self, id: str, usuario_id: str) -> None: ...

    @abstractmethod
    def historial_por_anio(self, usuario_id: str) -> dict: ...
