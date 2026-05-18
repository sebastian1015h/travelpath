from abc import ABC, abstractmethod
from src.application.dtos.usuario_dto import LoginDTO, RegisterDTO, UsuarioResponseDTO


class UsuarioServicePort(ABC):

    @abstractmethod
    def registrar(self, dto: RegisterDTO) -> UsuarioResponseDTO: ...

    @abstractmethod
    def login(self, dto: LoginDTO) -> dict: ...

    @abstractmethod
    def obtener_por_id(self, usuario_id: str) -> UsuarioResponseDTO: ...
