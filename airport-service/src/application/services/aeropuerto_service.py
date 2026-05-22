import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort
from src.application.dtos.aeropuerto_dto import AeropuertoDTO

logger = logging.getLogger(__name__)

PAGINAS_MAPA = [
    1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 105,
    113, 121, 129, 137, 145, 153, 161, 169, 177, 185, 193,
    201, 209, 217, 225, 233,
]


class AeropuertoService:

    def __init__(self, client: AeropuertoClientPort):
        self._client = client

    def buscar_por_nombre(self, nombre: str) -> List[AeropuertoDTO]:
        return self._client.buscar_por_nombre(nombre)

    def buscar_por_iata(self, iata: str) -> Optional[AeropuertoDTO]:
        return self._client.buscar_por_iata(iata)

    def listar_para_mapa(self) -> List[AeropuertoDTO]:
        aeropuertos: List[AeropuertoDTO] = []
        with ThreadPoolExecutor(max_workers=31) as executor:
            futures = [
                executor.submit(self._client.listar_aeropuertos, p)
                for p in PAGINAS_MAPA
            ]
            futures.append(executor.submit(self._client.listar_colombia))
            for future in as_completed(futures):
                try:
                    aeropuertos.extend(future.result())
                except Exception as ex:
                    logger.warning("Error al obtener página de aeropuertos: %s", ex)

        vistos: set = set()
        unicos: List[AeropuertoDTO] = []
        for a in aeropuertos:
            if a.iata not in vistos and a.latitud and a.longitud:
                vistos.add(a.iata)
                unicos.append(a)
        return unicos
