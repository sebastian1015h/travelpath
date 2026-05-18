import unicodedata
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime
from typing import List, Optional

from src.application.dtos.aeropuerto_dto import AeropuertoDTO
from database.models.orm_models import AeropuertoCacheModel


def _norm(texto: str) -> str:
    """Quita acentos y convierte a mayúsculas para búsqueda tolerante."""
    sin_acentos = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return sin_acentos.upper()


class AeropuertoCacheService:

    def __init__(self, session: Session):
        self._session = session

    def guardar_o_actualizar(self, dto: AeropuertoDTO) -> None:
        existing = self._session.get(AeropuertoCacheModel, dto.iata.upper())
        if existing:
            existing.nombre = dto.nombre
            existing.ciudad = dto.ciudad
            existing.pais = dto.pais
            existing.latitud = dto.latitud
            existing.longitud = dto.longitud
            existing.consultado_at = datetime.utcnow()
        else:
            model = AeropuertoCacheModel(
                iata_code=dto.iata.upper(),
                nombre=dto.nombre,
                ciudad=dto.ciudad,
                pais=dto.pais,
                latitud=dto.latitud,
                longitud=dto.longitud,
            )
            self._session.add(model)
        self._session.commit()

    def buscar_por_texto(self, texto: str) -> List[AeropuertoDTO]:
        """Búsqueda local tolerante a acentos: IATA, ciudad, nombre o país."""
        q_orig = f"%{texto.upper()}%"
        q_norm = f"%{_norm(texto)}%"

        # Dos pasadas: primero con el texto original, luego normalizado sin acentos.
        # Esto permite que "Paris" encuentre "Paris" y "París" encuentre "Paris".
        condiciones = or_(
            func.upper(AeropuertoCacheModel.iata_code).like(q_orig),
            func.upper(AeropuertoCacheModel.nombre).like(q_orig),
            func.upper(AeropuertoCacheModel.ciudad).like(q_orig),
            func.upper(AeropuertoCacheModel.pais).like(q_orig),
        )
        if q_norm != q_orig:
            condiciones = or_(
                condiciones,
                func.upper(AeropuertoCacheModel.iata_code).like(q_norm),
                func.upper(AeropuertoCacheModel.nombre).like(q_norm),
                func.upper(AeropuertoCacheModel.ciudad).like(q_norm),
                func.upper(AeropuertoCacheModel.pais).like(q_norm),
            )

        models = (
            self._session.query(AeropuertoCacheModel)
            .filter(condiciones)
            .order_by(AeropuertoCacheModel.iata_code)
            .limit(12)
            .all()
        )
        return [self._to_dto(m) for m in models]

    def obtener_por_iata(self, iata: str) -> Optional[AeropuertoDTO]:
        model = self._session.get(AeropuertoCacheModel, iata.upper())
        return self._to_dto(model) if model else None

    def listar_todos(self) -> List[AeropuertoDTO]:
        models = self._session.query(AeropuertoCacheModel).all()
        return [self._to_dto(m) for m in models]

    def _to_dto(self, model: AeropuertoCacheModel) -> AeropuertoDTO:
        return AeropuertoDTO(
            iata=model.iata_code,
            nombre=model.nombre,
            ciudad=model.ciudad,
            pais=model.pais,
            latitud=model.latitud,
            longitud=model.longitud,
        )
