from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort


def create_aeropuerto_blueprint(aeropuerto_client: AeropuertoClientPort) -> Blueprint:
    aeropuerto_bp = Blueprint("aeropuertos", __name__, url_prefix="/api/aeropuertos")

    @aeropuerto_bp.get("")
    @jwt_required()
    def buscar_por_nombre():
        nombre = request.args.get("nombre", "").strip()
        if not nombre or len(nombre) < 2:
            return jsonify({"error": "Ingresa al menos 2 caracteres."}), 400
        try:
            resultados = aeropuerto_client.buscar_por_nombre(nombre)
        except Exception:
            return jsonify({"error": "No se pudo conectar con el servicio de aeropuertos."}), 503
        return jsonify([r.to_dict() for r in resultados[:12]]), 200

    @aeropuerto_bp.get("/mapa")
    @jwt_required()
    def datos_mapa():
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 30 páginas distribuidas uniformemente sobre las ~250 de AirportGap
        paginas_gap = [1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 105,
                       113, 121, 129, 137, 145, 153, 161, 169, 177, 185, 193,
                       201, 209, 217, 225, 233]

        aeropuertos = []
        with ThreadPoolExecutor(max_workers=31) as executor:
            futures = [executor.submit(aeropuerto_client.listar_aeropuertos, p) for p in paginas_gap]
            futures.append(executor.submit(aeropuerto_client.listar_colombia))
            for future in as_completed(futures):
                try:
                    aeropuertos.extend(future.result())
                except Exception:
                    pass

        vistos = set()
        unicos = []
        for a in aeropuertos:
            if a.iata not in vistos and a.latitud and a.longitud:
                vistos.add(a.iata)
                unicos.append(a)
        return jsonify([a.to_dict() for a in unicos]), 200

    @aeropuerto_bp.get("/<string:iata>")
    @jwt_required()
    def buscar_por_iata(iata: str):
        if len(iata) != 3:
            return jsonify({"error": "El código IATA debe tener exactamente 3 letras."}), 400
        resultado = aeropuerto_client.buscar_por_iata(iata.upper())
        if resultado:
            return jsonify(resultado.to_dict()), 200
        return jsonify({"error": f"Aeropuerto '{iata.upper()}' no encontrado."}), 404

    return aeropuerto_bp
