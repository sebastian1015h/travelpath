from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort
from src.application.services.aeropuerto_cache_service import AeropuertoCacheService


def create_aeropuerto_blueprint(
    aeropuerto_client: AeropuertoClientPort,
    cache_service: AeropuertoCacheService = None,
) -> Blueprint:
    aeropuerto_bp = Blueprint("aeropuertos", __name__, url_prefix="/api/aeropuertos")

    @aeropuerto_bp.get("")
    @jwt_required()
    def buscar_por_nombre():
        nombre = request.args.get("nombre", "").strip()
        if not nombre or len(nombre) < 2:
            return jsonify({"error": "Ingresa al menos 2 caracteres."}), 400

        resultados = []

        # 1. Búsqueda local en BD (rápida, siempre disponible)
        if cache_service:
            resultados = cache_service.buscar_por_texto(nombre)

        # 2. Si hay pocos resultados locales, complementa con la API externa
        if len(resultados) < 4:
            try:
                externos = aeropuerto_client.buscar_por_nombre(nombre)
                iatas_existentes = {r.iata for r in resultados}
                for a in externos:
                    if a.iata not in iatas_existentes:
                        resultados.append(a)
                        # Guardar en caché para próximas búsquedas
                        if cache_service and a.latitud and a.longitud:
                            try:
                                cache_service.guardar_o_actualizar(a)
                            except Exception:
                                pass
            except Exception:
                pass  # La API falló, devolvemos solo los locales

        return jsonify([r.to_dict() for r in resultados[:12]]), 200

    @aeropuerto_bp.get("/mapa")
    @jwt_required()
    def datos_mapa():
        aeropuertos = cache_service.listar_todos() if cache_service else []
        return jsonify([a.to_dict() for a in aeropuertos]), 200

    @aeropuerto_bp.get("/<string:iata>")
    @jwt_required()
    def buscar_por_iata(iata: str):
        if len(iata) != 3:
            return jsonify({"error": "El código IATA debe tener exactamente 3 letras."}), 400

        iata = iata.upper()

        # 1. Caché local primero
        if cache_service:
            resultado = cache_service.obtener_por_iata(iata)
            if resultado:
                return jsonify(resultado.to_dict()), 200

        # 2. API externa
        try:
            resultado = aeropuerto_client.buscar_por_iata(iata)
            if resultado:
                if cache_service and resultado.latitud:
                    try:
                        cache_service.guardar_o_actualizar(resultado)
                    except Exception:
                        pass
                return jsonify(resultado.to_dict()), 200
        except Exception:
            pass

        return jsonify({"error": f"Aeropuerto '{iata}' no encontrado."}), 404

    return aeropuerto_bp
