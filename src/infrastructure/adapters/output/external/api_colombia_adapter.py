import logging
from typing import List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort
from src.application.dtos.aeropuerto_dto import AeropuertoDTO

logger = logging.getLogger(__name__)


class ApiColombiaAdapter(AeropuertoClientPort):
    """
    Fuente principal : AirportGap  (mundial)  https://airportgap.com/api/airports
    Fuente secundaria: API Colombia (solo COL) https://api-colombia.com/api/v1/Airport
    """

    AIRPORTGAP_URL = "https://airportgap.com/api/airports"
    COLOMBIA_URL   = "https://api-colombia.com/api/v1"

    def __init__(self):
        self._client = httpx.Client(timeout=12.0)

    # ── Búsqueda por nombre ──────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4),
           retry=retry_if_exception_type(httpx.HTTPError))
    def buscar_por_nombre(self, nombre: str) -> List[AeropuertoDTO]:
        # 1. AirportGap (mundial)
        try:
            res = self._client.get(self.AIRPORTGAP_URL, params={"q": nombre})
            res.raise_for_status()
            data = res.json().get("data", [])
            resultados = [self._mapear_gap(a) for a in data if self._iata_valida(a)]
            if resultados:
                return resultados[:10]
        except Exception as ex:
            logger.warning(f"AirportGap search falló: {ex}")

        # 2. Fallback: API Colombia
        try:
            res = self._client.get(f"{self.COLOMBIA_URL}/Airport/search/{nombre}")
            res.raise_for_status()
            data = res.json()
            return [self._mapear_colombia(a) for a in data if a.get("iataCode")][:10]
        except Exception as ex:
            logger.warning(f"API Colombia search falló: {ex}")

        return []

    # ── Búsqueda por IATA ────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4),
           retry=retry_if_exception_type(httpx.HTTPError))
    def buscar_por_iata(self, iata: str) -> Optional[AeropuertoDTO]:
        iata = iata.upper()

        # 1. AirportGap (REST by IATA)
        try:
            res = self._client.get(f"{self.AIRPORTGAP_URL}/{iata}")
            res.raise_for_status()
            data = res.json().get("data", {})
            if data:
                return self._mapear_gap(data)
        except Exception as ex:
            logger.warning(f"AirportGap IATA {iata} falló: {ex}")

        # 2. Fallback: recorre lista Colombia
        try:
            res = self._client.get(f"{self.COLOMBIA_URL}/Airport")
            res.raise_for_status()
            for a in res.json():
                if a.get("iataCode", "").upper() == iata:
                    return self._mapear_colombia(a)
        except Exception as ex:
            logger.warning(f"API Colombia IATA {iata} falló: {ex}")

        return None

    # ── Listado paginado ─────────────────────────────────────────────────────

    def listar_aeropuertos(self, pagina: int = 1) -> List[AeropuertoDTO]:
        try:
            res = self._client.get(self.AIRPORTGAP_URL, params={"page": pagina})
            res.raise_for_status()
            data = res.json().get("data", [])
            return [self._mapear_gap(a) for a in data if self._iata_valida(a)]
        except Exception as ex:
            logger.warning(f"AirportGap listar página {pagina} falló: {ex}")
            return []

    # ── Mapeadores ───────────────────────────────────────────────────────────

    def _mapear_gap(self, raw: dict) -> AeropuertoDTO:
        attrs = raw.get("attributes", raw)
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        return AeropuertoDTO(
            iata    = attrs.get("iata") or raw.get("id", ""),
            nombre  = attrs.get("name", ""),
            ciudad  = attrs.get("city", ""),
            pais    = attrs.get("country", ""),
            latitud = float(lat) if lat else None,
            longitud= float(lon) if lon else None,
        )

    def _mapear_colombia(self, raw: dict) -> AeropuertoDTO:
        city = raw.get("city") or {}
        ciudad = city.get("name", "") if isinstance(city, dict) else str(city)
        return AeropuertoDTO(
            iata    = raw.get("iataCode", ""),
            nombre  = raw.get("name", ""),
            ciudad  = ciudad,
            pais    = "Colombia",
            latitud = raw.get("latitude"),
            longitud= raw.get("longitude"),
        )

    def _iata_valida(self, raw: dict) -> bool:
        attrs = raw.get("attributes", raw)
        iata = attrs.get("iata") or raw.get("id", "")
        return bool(iata) and len(iata) == 3
