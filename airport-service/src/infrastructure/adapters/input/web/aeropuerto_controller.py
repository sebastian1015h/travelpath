from flask import Blueprint, request, jsonify

from src.application.services.aeropuerto_service import AeropuertoService


def create_aeropuerto_blueprint(service: AeropuertoService) -> Blueprint:
    bp = Blueprint("aeropuertos", __name__, url_prefix="/aeropuertos")

    @bp.get("")
    def buscar_por_nombre():
        """
        Busca aeropuertos por nombre, ciudad o código IATA.
        ---
        tags:
          - Aeropuertos
        parameters:
          - name: nombre
            in: query
            type: string
            required: true
            description: Nombre del aeropuerto, ciudad o código IATA (mínimo 2 caracteres)
            example: Bogotá
        responses:
          200:
            description: Lista de aeropuertos encontrados
            schema:
              type: array
              items:
                $ref: '#/definitions/Aeropuerto'
          400:
            description: Parámetro de búsqueda inválido
            schema:
              $ref: '#/definitions/Error'
          503:
            description: No se pudo conectar con la API externa
            schema:
              $ref: '#/definitions/Error'
        definitions:
          Aeropuerto:
            type: object
            properties:
              iata:
                type: string
                example: BOG
              nombre:
                type: string
                example: El Dorado International Airport
              ciudad:
                type: string
                example: Bogotá
              pais:
                type: string
                example: Colombia
              latitud:
                type: number
                example: 4.7016
              longitud:
                type: number
                example: -74.1469
          Error:
            type: object
            properties:
              error:
                type: string
                example: Mensaje de error
        """
        nombre = request.args.get("nombre", "").strip()
        if not nombre or len(nombre) < 2:
            return jsonify({"error": "Ingresa al menos 2 caracteres."}), 400
        try:
            resultados = service.buscar_por_nombre(nombre)
        except Exception:
            return jsonify({"error": "No se pudo conectar con la API de aeropuertos."}), 503
        return jsonify([r.to_dict() for r in resultados[:12]]), 200

    @bp.get("/mapa")
    def datos_mapa():
        """
        Retorna todos los aeropuertos disponibles para renderizar en el mapa Plotly.
        ---
        tags:
          - Aeropuertos
        responses:
          200:
            description: Lista completa de aeropuertos con coordenadas
            schema:
              type: array
              items:
                $ref: '#/definitions/Aeropuerto'
          503:
            description: Error al obtener datos del mapa
            schema:
              $ref: '#/definitions/Error'
        """
        try:
            aeropuertos = service.listar_para_mapa()
            return jsonify([a.to_dict() for a in aeropuertos]), 200
        except Exception:
            return jsonify({"error": "Error al obtener datos para el mapa."}), 503

    @bp.get("/<string:iata>")
    def buscar_por_iata(iata: str):
        """
        Busca un aeropuerto por su código IATA.
        ---
        tags:
          - Aeropuertos
        parameters:
          - name: iata
            in: path
            type: string
            required: true
            description: Código IATA del aeropuerto (exactamente 3 letras)
            example: BOG
        responses:
          200:
            description: Aeropuerto encontrado
            schema:
              $ref: '#/definitions/Aeropuerto'
          400:
            description: Código IATA inválido (debe tener 3 letras)
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Aeropuerto no encontrado
            schema:
              $ref: '#/definitions/Error'
        """
        if len(iata) != 3:
            return jsonify({"error": "El código IATA debe tener exactamente 3 letras."}), 400
        resultado = service.buscar_por_iata(iata.upper())
        if resultado:
            return jsonify(resultado.to_dict()), 200
        return jsonify({"error": f"Aeropuerto '{iata.upper()}' no encontrado."}), 404

    return bp
