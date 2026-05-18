import logging
from collections import defaultdict
from typing import List

from src.domain.entities.itinerario import Itinerario
from src.domain.ports.output.itinerario_repository_port import ItinerarioRepositoryPort
from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort
from src.domain.exceptions.domain_exceptions import (
    ItinerarioNoEncontradoException,
    ItinerarioPasadoException,
    SuperposicionDeViajesException,
    AeropuertoNoEncontradoException,
)
from src.application.dtos.itinerario_dto import (
    CrearItinerarioDTO,
    ModificarItinerarioDTO,
    ItinerarioResponseDTO,
)
from src.application.dtos.aeropuerto_dto import AeropuertoDTO

logger = logging.getLogger(__name__)


class ItinerarioService:

    def __init__(
        self,
        itinerario_repo: ItinerarioRepositoryPort,
        aeropuerto_client: AeropuertoClientPort,
        aeropuerto_cache_repo=None,
    ):
        self._repo = itinerario_repo
        self._aeropuerto_client = aeropuerto_client
        self._aeropuerto_cache_repo = aeropuerto_cache_repo

    def crear(self, dto: CrearItinerarioDTO, usuario_id: str) -> ItinerarioResponseDTO:
        origen = self._obtener_aeropuerto(dto.aeropuerto_origen_iata)
        destino = self._obtener_aeropuerto(dto.aeropuerto_destino_iata)

        self._cachear_aeropuerto(origen)
        self._cachear_aeropuerto(destino)

        salida_iso = dto.fecha_hora_salida.isoformat()
        llegada_iso = dto.fecha_hora_llegada.isoformat()
        if self._repo.existe_superposicion(usuario_id, salida_iso, llegada_iso):
            raise SuperposicionDeViajesException(
                "Ya tienes un viaje planificado en ese rango de fechas."
            )

        itinerario = Itinerario(
            usuario_id=usuario_id,
            aeropuerto_origen_iata=dto.aeropuerto_origen_iata.upper(),
            aeropuerto_destino_iata=dto.aeropuerto_destino_iata.upper(),
            fecha_hora_salida=dto.fecha_hora_salida,
            fecha_hora_llegada=dto.fecha_hora_llegada,
            notas=dto.notas,
        )
        guardado = self._repo.guardar(itinerario)
        return self._to_dto(guardado, origen, destino)

    def listar_por_usuario(self, usuario_id: str) -> List[ItinerarioResponseDTO]:
        itinerarios = self._repo.listar_por_usuario(usuario_id)
        return [self._enriquecer(i) for i in itinerarios]

    def obtener_detalle(self, id: str, usuario_id: str) -> ItinerarioResponseDTO:
        itinerario = self._repo.obtener_por_id(id)
        if not itinerario or itinerario.usuario_id != usuario_id:
            raise ItinerarioNoEncontradoException(f"Itinerario '{id}' no encontrado.")
        return self._enriquecer(itinerario)

    def modificar(
        self, id: str, dto: ModificarItinerarioDTO, usuario_id: str
    ) -> ItinerarioResponseDTO:
        itinerario = self._repo.obtener_por_id(id)
        if not itinerario or itinerario.usuario_id != usuario_id:
            raise ItinerarioNoEncontradoException(f"Itinerario '{id}' no encontrado.")

        if itinerario.es_pasado():
            raise ItinerarioPasadoException("No se puede modificar un itinerario pasado.")

        if dto.aeropuerto_origen_iata:
            itinerario.aeropuerto_origen_iata = dto.aeropuerto_origen_iata.upper()
            self._cachear_aeropuerto(self._obtener_aeropuerto(dto.aeropuerto_origen_iata))
        if dto.aeropuerto_destino_iata:
            itinerario.aeropuerto_destino_iata = dto.aeropuerto_destino_iata.upper()
            self._cachear_aeropuerto(self._obtener_aeropuerto(dto.aeropuerto_destino_iata))
        if dto.fecha_hora_salida:
            itinerario.fecha_hora_salida = dto.fecha_hora_salida
        if dto.fecha_hora_llegada:
            itinerario.fecha_hora_llegada = dto.fecha_hora_llegada
        if dto.notas is not None:
            itinerario.notas = dto.notas

        itinerario._validar()

        salida_iso = itinerario.fecha_hora_salida.isoformat()
        llegada_iso = itinerario.fecha_hora_llegada.isoformat()
        if self._repo.existe_superposicion(usuario_id, salida_iso, llegada_iso, excluir_id=id):
            raise SuperposicionDeViajesException(
                "Ya tienes un viaje planificado en ese rango de fechas."
            )

        actualizado = self._repo.actualizar(itinerario)
        return self._enriquecer(actualizado)

    def eliminar(self, id: str, usuario_id: str) -> None:
        itinerario = self._repo.obtener_por_id(id)
        if not itinerario or itinerario.usuario_id != usuario_id:
            raise ItinerarioNoEncontradoException(f"Itinerario '{id}' no encontrado.")
        self._repo.eliminar_logico(id)

    def historial_por_anio(self, usuario_id: str) -> dict:
        itinerarios = self._repo.listar_por_usuario(usuario_id)
        historial = defaultdict(list)
        for it in itinerarios:
            anio = it.fecha_hora_salida.year
            enriquecido = self._enriquecer(it)
            historial[str(anio)].append(enriquecido.to_dict())
        return dict(sorted(historial.items(), reverse=True))

    def _obtener_aeropuerto(self, iata: str) -> AeropuertoDTO:
        aeropuerto = self._aeropuerto_client.buscar_por_iata(iata)
        if not aeropuerto:
            raise AeropuertoNoEncontradoException(
                f"No se encontró el aeropuerto con código IATA '{iata}'."
            )
        return aeropuerto

    def _cachear_aeropuerto(self, dto: AeropuertoDTO) -> None:
        if self._aeropuerto_cache_repo:
            try:
                self._aeropuerto_cache_repo.guardar_o_actualizar(dto)
            except Exception as ex:
                logger.warning(f"No se pudo cachear aeropuerto {dto.iata}: {ex}")

    def _enriquecer(self, itinerario: Itinerario) -> ItinerarioResponseDTO:
        origen = self._resolver_aeropuerto(itinerario.aeropuerto_origen_iata)
        destino = self._resolver_aeropuerto(itinerario.aeropuerto_destino_iata)
        return self._to_dto(itinerario, origen, destino)

    def _resolver_aeropuerto(self, iata: str) -> AeropuertoDTO:
        # 1. Buscar en caché local (tiene coordenadas del seed)
        if self._aeropuerto_cache_repo:
            try:
                cached = self._aeropuerto_cache_repo.obtener_por_iata(iata)
                if cached:
                    return cached
            except Exception:
                pass
        # 2. Fallback a la API externa
        try:
            resultado = self._aeropuerto_client.buscar_por_iata(iata)
            if resultado:
                return resultado
        except Exception:
            pass
        return AeropuertoDTO(iata=iata, nombre=iata, ciudad="", pais="")

    def _to_dto(
        self,
        itinerario: Itinerario,
        origen: AeropuertoDTO,
        destino: AeropuertoDTO,
    ) -> ItinerarioResponseDTO:
        delta = itinerario.fecha_hora_llegada - itinerario.fecha_hora_salida
        duracion = int(delta.total_seconds() / 60)
        return ItinerarioResponseDTO(
            id=itinerario.id,
            usuario_id=itinerario.usuario_id,
            aeropuerto_origen=origen,
            aeropuerto_destino=destino,
            fecha_hora_salida=itinerario.fecha_hora_salida,
            fecha_hora_llegada=itinerario.fecha_hora_llegada,
            duracion_minutos=duracion,
            notas=itinerario.notas,
            activo=itinerario.activo,
            created_at=itinerario.created_at,
        )
