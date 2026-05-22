import logging
from typing import List, Optional

import httpx

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort
from src.application.dtos.aeropuerto_dto import AeropuertoDTO

logger = logging.getLogger(__name__)


class AirportServiceHttpAdapter(AeropuertoClientPort):
    """Adapter que implementa AeropuertoClientPort comunicándose con el airport-service via HTTP."""

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")
        self._timeout = 10.0

    def buscar_por_nombre(self, nombre: str) -> List[AeropuertoDTO]:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.get(
                    f"{self._base_url}/aeropuertos",
                    params={"nombre": nombre},
                )
            res.raise_for_status()
            return [self._mapear(a) for a in res.json()]
        except Exception as ex:
            logger.warning("AirportService buscar_por_nombre falló: %s", ex)
            return []

    def buscar_por_iata(self, iata: str) -> Optional[AeropuertoDTO]:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.get(f"{self._base_url}/aeropuertos/{iata.upper()}")
            if res.status_code == 404:
                return None
            res.raise_for_status()
            return self._mapear(res.json())
        except Exception as ex:
            logger.warning("AirportService buscar_por_iata %s falló: %s", iata, ex)
            return None

    def listar_aeropuertos(self, pagina: int = 1) -> List[AeropuertoDTO]:
        """Delega al endpoint /mapa del airport-service que ya agrega todos los aeropuertos."""
        if pagina != 1:
            return []
        try:
            with httpx.Client(timeout=120.0) as client:
                res = client.get(f"{self._base_url}/aeropuertos/mapa")
            res.raise_for_status()
            return [self._mapear(a) for a in res.json()]
        except Exception as ex:
            logger.warning("AirportService listar_para_mapa falló: %s", ex)
            return []

    def listar_colombia(self) -> List[AeropuertoDTO]:
        return []

    def _mapear(self, data: dict) -> AeropuertoDTO:
        return AeropuertoDTO(
            iata     = data.get("iata", ""),
            nombre   = data.get("nombre", ""),
            ciudad   = data.get("ciudad", ""),
            pais     = data.get("pais", ""),
            latitud  = data.get("latitud"),
            longitud = data.get("longitud"),
        )
