from typing import Optional
from sqlalchemy.orm import Session

from src.domain.entities.usuario import Usuario
from src.domain.ports.output.usuario_repository_port import UsuarioRepositoryPort
from database.models.orm_models import UsuarioModel


class SQLAlchemyUsuarioRepo(UsuarioRepositoryPort):

    def __init__(self, session: Session):
        self._session = session

    def guardar(self, usuario: Usuario) -> Usuario:
        model = UsuarioModel(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            contrasena_hash=usuario.contrasena_hash,
            activo=usuario.activo,
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def obtener_por_id(self, id: str) -> Optional[Usuario]:
        model = self._session.get(UsuarioModel, id)
        return self._to_entity(model) if model else None

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        model = (
            self._session.query(UsuarioModel)
            .filter(UsuarioModel.correo == correo)
            .first()
        )
        return self._to_entity(model) if model else None

    def existe_por_correo(self, correo: str) -> bool:
        return (
            self._session.query(UsuarioModel)
            .filter(UsuarioModel.correo == correo)
            .count()
        ) > 0

    def actualizar(self, usuario: Usuario) -> Usuario:
        model = self._session.get(UsuarioModel, usuario.id)
        if model:
            model.nombre = usuario.nombre
            model.correo = usuario.correo
            model.contrasena_hash = usuario.contrasena_hash
            model.activo = usuario.activo
            model.updated_at = usuario.updated_at
            self._session.commit()
            self._session.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: UsuarioModel) -> Usuario:
        return Usuario(
            id=model.id,
            nombre=model.nombre,
            correo=model.correo,
            contrasena_hash=model.contrasena_hash,
            activo=model.activo,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
