import logging
from typing import List, Optional

import httpx

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort
from src.application.dtos.aeropuerto_dto import AeropuertoDTO

logger = logging.getLogger(__name__)

AIRPORTGAP_URL = "https://airportgap.com/api/airports"
COLOMBIA_URL   = "https://api-colombia.com/api/v1"
TIMEOUT        = 5.0


class ApiColombiaAdapter(AeropuertoClientPort):

    def buscar_por_nombre(self, nombre: str) -> List[AeropuertoDTO]:
        q = nombre.strip()
        q_upper = q.upper()

        if len(q_upper) == 3 and q_upper.isalpha():
            try:
                resultado = self.buscar_por_iata(q_upper)
                if resultado:
                    return [resultado]
            except Exception:
                pass

        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                res = client.get(AIRPORTGAP_URL, params={"q": q})
            res.raise_for_status()
            data = res.json().get("data", [])
            resultados = [self._mapear_gap(a) for a in data if self._iata_valida(a)]
            if resultados:
                return resultados[:10]
        except Exception as ex:
            logger.warning("AirportGap buscar_por_nombre falló: %s", ex)

        try:
            colombianos = self.listar_colombia()
            encontrados = [
                a for a in colombianos
                if q_upper in a.iata.upper()
                or q_upper in a.nombre.upper()
                or q_upper in a.ciudad.upper()
            ]
            if encontrados:
                return encontrados[:10]
        except Exception as ex:
            logger.warning("Búsqueda local Colombia falló: %s", ex)

        return []

    def buscar_por_iata(self, iata: str) -> Optional[AeropuertoDTO]:
        iata = iata.upper()

        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                res = client.get(f"{AIRPORTGAP_URL}/{iata}")
            res.raise_for_status()
            data = res.json().get("data", {})
            if data:
                return self._mapear_gap(data)
        except Exception as ex:
            logger.warning("AirportGap buscar_por_iata %s falló: %s", iata, ex)

        try:
            colombianos = self.listar_colombia()
            for a in colombianos:
                if a.iata.upper() == iata:
                    return a
        except Exception as ex:
            logger.warning("API Colombia buscar_por_iata %s falló: %s", iata, ex)

        return None

    def listar_aeropuertos(self, pagina: int = 1) -> List[AeropuertoDTO]:
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                res = client.get(AIRPORTGAP_URL, params={"page": pagina})
            res.raise_for_status()
            data = res.json().get("data", [])
            return [self._mapear_gap(a) for a in data if self._iata_valida(a)]
        except Exception as ex:
            logger.warning("AirportGap listar página %s falló: %s", pagina, ex)
            return []

    def listar_colombia(self) -> List[AeropuertoDTO]:
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                res = client.get(f"{COLOMBIA_URL}/Airport")
            res.raise_for_status()
            return [
                self._mapear_colombia(a) for a in res.json()
                if a.get("iataCode") and a.get("latitude") and a.get("longitude")
            ]
        except Exception as ex:
            logger.warning("API Colombia listar_colombia falló: %s", ex)
            return []

    def _mapear_gap(self, raw: dict) -> AeropuertoDTO:
        attrs = raw.get("attributes", raw)
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        return AeropuertoDTO(
            iata     = attrs.get("iata") or raw.get("id", ""),
            nombre   = attrs.get("name", ""),
            ciudad   = attrs.get("city", ""),
            pais     = attrs.get("country", ""),
            latitud  = float(lat) if lat else None,
            longitud = float(lon) if lon else None,
        )

    def _mapear_colombia(self, raw: dict) -> AeropuertoDTO:
        city = raw.get("city") or {}
        ciudad = city.get("name", "") if isinstance(city, dict) else str(city)
        return AeropuertoDTO(
            iata     = raw.get("iataCode", ""),
            nombre   = raw.get("name", ""),
            ciudad   = ciudad,
            pais     = "Colombia",
            latitud  = raw.get("latitude"),
            longitud = raw.get("longitude"),
        )

    def _iata_valida(self, raw: dict) -> bool:
        attrs = raw.get("attributes", raw)
        iata = attrs.get("iata") or raw.get("id", "")
        return bool(iata) and len(iata) == 3
