from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.domain.entities.itinerario import Itinerario
from src.domain.ports.output.itinerario_repository_port import ItinerarioRepositoryPort
from database.models.orm_models import ItinerarioModel


class SQLAlchemyItinerarioRepo(ItinerarioRepositoryPort):

    def __init__(self, session: Session):
        self._session = session

    def guardar(self, itinerario: Itinerario) -> Itinerario:
        try:
            model = ItinerarioModel(
                id=itinerario.id,
                usuario_id=itinerario.usuario_id,
                aeropuerto_origen_iata=itinerario.aeropuerto_origen_iata.upper(),
                aeropuerto_destino_iata=itinerario.aeropuerto_destino_iata.upper(),
                fecha_hora_salida=itinerario.fecha_hora_salida,
                fecha_hora_llegada=itinerario.fecha_hora_llegada,
                duracion_minutos=itinerario.calcular_duracion(),
                notas=itinerario.notas,
                activo=itinerario.activo,
                created_at=itinerario.created_at,
                updated_at=itinerario.updated_at,
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return self._to_entity(model)
        except Exception:
            self._session.rollback()
            raise

    def obtener_por_id(self, id: str) -> Optional[Itinerario]:
        model = (
            self._session.query(ItinerarioModel)
            .filter(ItinerarioModel.id == id, ItinerarioModel.activo == True)
            .first()
        )
        return self._to_entity(model) if model else None

    def listar_por_usuario(self, usuario_id: str) -> List[Itinerario]:
        models = (
            self._session.query(ItinerarioModel)
            .filter(
                ItinerarioModel.usuario_id == usuario_id,
                ItinerarioModel.activo == True,
            )
            .order_by(ItinerarioModel.fecha_hora_salida.asc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def actualizar(self, itinerario: Itinerario) -> Itinerario:
        try:
            model = self._session.get(ItinerarioModel, itinerario.id)
            if model:
                model.aeropuerto_origen_iata = itinerario.aeropuerto_origen_iata.upper()
                model.aeropuerto_destino_iata = itinerario.aeropuerto_destino_iata.upper()
                model.fecha_hora_salida = itinerario.fecha_hora_salida
                model.fecha_hora_llegada = itinerario.fecha_hora_llegada
                model.duracion_minutos = itinerario.calcular_duracion()
                model.notas = itinerario.notas
                model.activo = itinerario.activo
                model.updated_at = datetime.utcnow()
                self._session.commit()
                self._session.refresh(model)
            return self._to_entity(model)
        except Exception:
            self._session.rollback()
            raise

    def eliminar_logico(self, id: str) -> None:
        try:
            model = self._session.get(ItinerarioModel, id)
            if model:
                model.activo = False
                model.updated_at = datetime.utcnow()
                self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def existe_superposicion(
        self, usuario_id: str, salida: str, llegada: str, excluir_id: str = None
    ) -> bool:
        salida_dt = datetime.fromisoformat(salida)
        llegada_dt = datetime.fromisoformat(llegada)

        query = self._session.query(ItinerarioModel).filter(
            ItinerarioModel.usuario_id == usuario_id,
            ItinerarioModel.activo == True,
            or_(
                and_(
                    ItinerarioModel.fecha_hora_salida < llegada_dt,
                    ItinerarioModel.fecha_hora_llegada > salida_dt,
                )
            ),
        )
        if excluir_id:
            query = query.filter(ItinerarioModel.id != excluir_id)
        return query.count() > 0

    def _to_entity(self, model: ItinerarioModel) -> Itinerario:
        itinerario = object.__new__(Itinerario)
        itinerario.id = model.id
        itinerario.usuario_id = model.usuario_id
        itinerario.aeropuerto_origen_iata = model.aeropuerto_origen_iata
        itinerario.aeropuerto_destino_iata = model.aeropuerto_destino_iata
        itinerario.fecha_hora_salida = model.fecha_hora_salida
        itinerario.fecha_hora_llegada = model.fecha_hora_llegada
        itinerario.notas = model.notas or ""
        itinerario.activo = model.activo
        itinerario.created_at = model.created_at
        itinerario.updated_at = model.updated_at
        return itinerario
