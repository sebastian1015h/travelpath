from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.itinerario import Itinerario


class ItinerarioRepositoryPort(ABC):

    @abstractmethod
    def guardar(self, itinerario: Itinerario) -> Itinerario: ...

    @abstractmethod
    def obtener_por_id(self, id: str) -> Optional[Itinerario]: ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str) -> List[Itinerario]: ...

    @abstractmethod
    def actualizar(self, itinerario: Itinerario) -> Itinerario: ...

    @abstractmethod
    def eliminar_logico(self, id: str) -> None: ...

    @abstractmethod
    def existe_superposicion(
        self, usuario_id: str, salida: str, llegada: str, excluir_id: str = None
    ) -> bool: ...
