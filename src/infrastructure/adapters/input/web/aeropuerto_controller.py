from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from src.domain.ports.output.aeropuerto_client_port import AeropuertoClientPort


def create_aeropuerto_blueprint(aeropuerto_client: AeropuertoClientPort) -> Blueprint:
    aeropuerto_bp = Blueprint("aeropuertos", __name__, url_prefix="/api/aeropuertos")

    @aeropuerto_bp.get("")
    @jwt_required()
    def buscar_por_nombre():
        """
        Busca aeropuertos por nombre, ciudad o código IATA (proxy al Airport Service).
        ---
        tags:
          - Aeropuertos
        security:
          - Bearer: []
        parameters:
          - name: nombre
            in: query
            type: string
            required: true
            description: Nombre del aeropuerto, ciudad o código IATA (mínimo 2 caracteres)
            example: Medellín
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
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
          503:
            description: No se pudo conectar con el Airport Service
            schema:
              $ref: '#/definitions/Error'
        definitions:
          Aeropuerto:
            type: object
            properties:
              iata:
                type: string
                example: MDE
              nombre:
                type: string
                example: José María Córdova International Airport
              ciudad:
                type: string
                example: Medellín
              pais:
                type: string
                example: Colombia
              latitud:
                type: number
                example: 6.1645
              longitud:
                type: number
                example: -75.4231
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
            resultados = aeropuerto_client.buscar_por_nombre(nombre)
        except Exception:
            return jsonify({"error": "No se pudo conectar con el servicio de aeropuertos."}), 503
        return jsonify([r.to_dict() for r in resultados[:12]]), 200

    @aeropuerto_bp.get("/mapa")
    @jwt_required()
    def datos_mapa():
        """
        Retorna todos los aeropuertos para renderizar el mapa Plotly (proxy al Airport Service).
        ---
        tags:
          - Aeropuertos
        security:
          - Bearer: []
        responses:
          200:
            description: Lista completa de aeropuertos con coordenadas
            schema:
              type: array
              items:
                $ref: '#/definitions/Aeropuerto'
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
          503:
            description: No se pudo conectar con el Airport Service
            schema:
              $ref: '#/definitions/Error'
        """
        try:
            aeropuertos = aeropuerto_client.listar_aeropuertos()
        except Exception:
            return jsonify({"error": "No se pudo conectar con el servicio de aeropuertos."}), 503
        return jsonify([a.to_dict() for a in aeropuertos]), 200

    @aeropuerto_bp.get("/<string:iata>")
    @jwt_required()
    def buscar_por_iata(iata: str):
        """
        Busca un aeropuerto por su código IATA (proxy al Airport Service).
        ---
        tags:
          - Aeropuertos
        security:
          - Bearer: []
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
            description: Código IATA inválido
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Aeropuerto no encontrado
            schema:
              $ref: '#/definitions/Error'
        """
        if len(iata) != 3:
            return jsonify({"error": "El código IATA debe tener exactamente 3 letras."}), 400
        resultado = aeropuerto_client.buscar_por_iata(iata.upper())
        if resultado:
            return jsonify(resultado.to_dict()), 200
        return jsonify({"error": f"Aeropuerto '{iata.upper()}' no encontrado."}), 404

    return aeropuerto_bp
