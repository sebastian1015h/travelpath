import logging
from datetime import timedelta

from flask_jwt_extended import create_access_token, create_refresh_token

from src.domain.entities.usuario import Usuario
from src.domain.ports.output.usuario_repository_port import UsuarioRepositoryPort
from src.domain.exceptions.domain_exceptions import (
    EmailYaRegistradoException,
    CredencialesInvalidasException,
    UsuarioNoEncontradoException,
)
from src.application.dtos.usuario_dto import RegisterDTO, LoginDTO, UsuarioResponseDTO
from src.infrastructure.security.password_handler import hashear, verificar

logger = logging.getLogger(__name__)

class AuthService:

    def __init__(self, usuario_repo: UsuarioRepositoryPort, token_blacklist=None):
        self._repo = usuario_repo
        self._blacklist = token_blacklist

    def registrar(self, dto: RegisterDTO) -> UsuarioResponseDTO:
        if self._repo.existe_por_correo(dto.correo):
            raise EmailYaRegistradoException(f"El correo '{dto.correo}' ya está registrado.")

        usuario = Usuario(
            nombre=dto.nombre,
            correo=dto.correo,
            contrasena_hash=hashear(dto.contrasena),
        )
        guardado = self._repo.guardar(usuario)
        logger.info(f"Usuario registrado: {guardado.correo}")
        return self._to_dto(guardado)

    def login(self, dto: LoginDTO) -> dict:
        usuario = self._repo.obtener_por_correo(dto.correo)
        if not usuario or not verificar(dto.contrasena, usuario.contrasena_hash):
            raise CredencialesInvalidasException("Correo o contraseña incorrectos.")

        expires_delta = timedelta(days=30) if dto.recordar else timedelta(hours=24)
        access_token = create_access_token(
            identity=usuario.id,
            additional_claims={"correo": usuario.correo, "nombre": usuario.nombre},
            expires_delta=expires_delta,
        )
        refresh_token = create_refresh_token(
            identity=usuario.id,
            expires_delta=timedelta(days=30),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "usuario": self._to_dto(usuario).to_dict(),
        }

    def logout(self, jti: str) -> None:
        if self._blacklist:
            self._blacklist.revocar(jti)

    def obtener_por_id(self, usuario_id: str) -> UsuarioResponseDTO:
        usuario = self._repo.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoException(f"Usuario '{usuario_id}' no encontrado.")
        return self._to_dto(usuario)

    def recuperar_contrasena(self, correo: str) -> str:
        usuario = self._repo.obtener_por_correo(correo)
        if not usuario:
            raise UsuarioNoEncontradoException("Correo no registrado.")
        token_temporal = f"RESET-{usuario.id[:8]}-TOKEN"
        logger.info(f"[DEV] Token de recuperación para {correo}: {token_temporal}")
        return token_temporal

    def _to_dto(self, usuario: Usuario) -> UsuarioResponseDTO:
        return UsuarioResponseDTO(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            activo=usuario.activo,
        )
