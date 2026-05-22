from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.usuario import Usuario


class UsuarioRepositoryPort(ABC):

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def obtener_por_id(self, id: str) -> Optional[Usuario]: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Usuario]: ...

    @abstractmethod
    def existe_por_correo(self, correo: str) -> bool: ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario: ...
