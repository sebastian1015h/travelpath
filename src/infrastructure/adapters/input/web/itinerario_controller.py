from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.application.services.itinerario_service import ItinerarioService
from src.application.dtos.itinerario_dto import CrearItinerarioDTO, ModificarItinerarioDTO
from src.domain.exceptions.domain_exceptions import (
    ItinerarioNoEncontradoException,
    ItinerarioPasadoException,
    SuperposicionDeViajesException,
    FechaInvalidaException,
    OrigenIgualDestinoException,
)


def _parse_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha inválido: {value}")


def create_itinerario_blueprint(itinerario_service: ItinerarioService) -> Blueprint:
    itinerario_bp = Blueprint("itinerarios", __name__, url_prefix="/api/itinerarios")

    @itinerario_bp.get("")
    @jwt_required()
    def listar():
        """
        Lista todos los itinerarios del usuario autenticado.
        ---
        tags:
          - Itinerarios
        security:
          - Bearer: []
        responses:
          200:
            description: Lista de itinerarios del usuario
            schema:
              type: array
              items:
                $ref: '#/definitions/Itinerario'
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
        definitions:
          AeropuertoResumen:
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
          Itinerario:
            type: object
            properties:
              id:
                type: string
                example: 550e8400-e29b-41d4-a716-446655440000
              usuario_id:
                type: string
                example: 550e8400-e29b-41d4-a716-446655440001
              aeropuerto_origen:
                $ref: '#/definitions/AeropuertoResumen'
              aeropuerto_destino:
                $ref: '#/definitions/AeropuertoResumen'
              fecha_hora_salida:
                type: string
                example: "2025-07-15T08:00:00"
              fecha_hora_llegada:
                type: string
                example: "2025-07-15T10:30:00"
              duracion_minutos:
                type: integer
                example: 150
              notas:
                type: string
                example: Ventana preferida
              activo:
                type: boolean
                example: true
          Error:
            type: object
            properties:
              error:
                type: string
                example: Mensaje de error
        """
        usuario_id = get_jwt_identity()
        itinerarios = itinerario_service.listar_por_usuario(usuario_id)
        return jsonify([i.to_dict() for i in itinerarios]), 200

    @itinerario_bp.post("")
    @jwt_required()
    def crear():
        """
        Crea un nuevo itinerario de viaje.
        ---
        tags:
          - Itinerarios
        security:
          - Bearer: []
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - aeropuerto_origen_iata
                - aeropuerto_destino_iata
                - fecha_hora_salida
                - fecha_hora_llegada
              properties:
                aeropuerto_origen_iata:
                  type: string
                  example: BOG
                aeropuerto_destino_iata:
                  type: string
                  example: MDE
                fecha_hora_salida:
                  type: string
                  example: "2025-07-15T08:00:00"
                fecha_hora_llegada:
                  type: string
                  example: "2025-07-15T10:30:00"
                notas:
                  type: string
                  example: Ventana preferida
        responses:
          201:
            description: Itinerario creado exitosamente
            schema:
              $ref: '#/definitions/Itinerario'
          400:
            description: Campos requeridos faltantes o formato de fecha inválido
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Ya existe un viaje planificado en ese rango de fechas
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Validación fallida (fecha llegada antes que salida, origen igual a destino)
            schema:
              $ref: '#/definitions/Error'
          500:
            description: Error interno del servidor
            schema:
              $ref: '#/definitions/Error'
        """
        usuario_id = get_jwt_identity()
        body = request.get_json(silent=True) or {}

        campos = ["aeropuerto_origen_iata", "aeropuerto_destino_iata", "fecha_hora_salida", "fecha_hora_llegada"]
        faltantes = [c for c in campos if not body.get(c)]
        if faltantes:
            return jsonify({"error": f"Campos requeridos: {', '.join(faltantes)}"}), 400

        try:
            dto = CrearItinerarioDTO(
                aeropuerto_origen_iata=body["aeropuerto_origen_iata"].upper(),
                aeropuerto_destino_iata=body["aeropuerto_destino_iata"].upper(),
                fecha_hora_salida=_parse_datetime(body["fecha_hora_salida"]),
                fecha_hora_llegada=_parse_datetime(body["fecha_hora_llegada"]),
                notas=body.get("notas", ""),
            )
            resultado = itinerario_service.crear(dto, usuario_id)
            return jsonify(resultado.to_dict()), 201
        except (FechaInvalidaException, OrigenIgualDestinoException) as e:
            return jsonify({"error": str(e)}), 422
        except SuperposicionDeViajesException as e:
            return jsonify({"error": str(e)}), 409
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "Error interno del servidor."}), 500

    @itinerario_bp.get("/historial")
    @jwt_required()
    def historial():
        """
        Retorna los itinerarios del usuario agrupados por año.
        ---
        tags:
          - Itinerarios
        security:
          - Bearer: []
        responses:
          200:
            description: Itinerarios agrupados por año (descendente)
            schema:
              type: object
              additionalProperties:
                type: array
                items:
                  $ref: '#/definitions/Itinerario'
              example:
                "2025": []
                "2024": []
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
        """
        usuario_id = get_jwt_identity()
        return jsonify(itinerario_service.historial_por_anio(usuario_id)), 200

    @itinerario_bp.get("/<string:id>")
    @jwt_required()
    def detalle(id):
        """
        Retorna el detalle de un itinerario específico.
        ---
        tags:
          - Itinerarios
        security:
          - Bearer: []
        parameters:
          - name: id
            in: path
            type: string
            required: true
            description: ID UUID del itinerario
            example: 550e8400-e29b-41d4-a716-446655440000
        responses:
          200:
            description: Detalle del itinerario
            schema:
              $ref: '#/definitions/Itinerario'
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Itinerario no encontrado
            schema:
              $ref: '#/definitions/Error'
        """
        usuario_id = get_jwt_identity()
        try:
            resultado = itinerario_service.obtener_detalle(id, usuario_id)
            return jsonify(resultado.to_dict()), 200
        except ItinerarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404

    @itinerario_bp.put("/<string:id>")
    @jwt_required()
    def modificar(id):
        """
        Modifica un itinerario existente (no se puede modificar si ya pasó).
        ---
        tags:
          - Itinerarios
        security:
          - Bearer: []
        parameters:
          - name: id
            in: path
            type: string
            required: true
            description: ID UUID del itinerario
            example: 550e8400-e29b-41d4-a716-446655440000
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                aeropuerto_origen_iata:
                  type: string
                  example: BOG
                aeropuerto_destino_iata:
                  type: string
                  example: CLO
                fecha_hora_salida:
                  type: string
                  example: "2025-08-20T09:00:00"
                fecha_hora_llegada:
                  type: string
                  example: "2025-08-20T11:00:00"
                notas:
                  type: string
                  example: Asiento pasillo
        responses:
          200:
            description: Itinerario modificado exitosamente
            schema:
              $ref: '#/definitions/Itinerario'
          400:
            description: Formato de fecha inválido
            schema:
              $ref: '#/definitions/Error'
          403:
            description: No se puede modificar un itinerario que ya pasó
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Itinerario no encontrado
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Superposición con otro viaje existente
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Validación fallida
            schema:
              $ref: '#/definitions/Error'
        """
        usuario_id = get_jwt_identity()
        body = request.get_json(silent=True) or {}

        try:
            dto = ModificarItinerarioDTO(
                aeropuerto_origen_iata=body.get("aeropuerto_origen_iata"),
                aeropuerto_destino_iata=body.get("aeropuerto_destino_iata"),
                fecha_hora_salida=_parse_datetime(body["fecha_hora_salida"]) if body.get("fecha_hora_salida") else None,
                fecha_hora_llegada=_parse_datetime(body["fecha_hora_llegada"]) if body.get("fecha_hora_llegada") else None,
                notas=body.get("notas"),
            )
            resultado = itinerario_service.modificar(id, dto, usuario_id)
            return jsonify(resultado.to_dict()), 200
        except ItinerarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404
        except ItinerarioPasadoException as e:
            return jsonify({"error": str(e)}), 403
        except (FechaInvalidaException, OrigenIgualDestinoException) as e:
            return jsonify({"error": str(e)}), 422
        except SuperposicionDeViajesException as e:
            return jsonify({"error": str(e)}), 409
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "Error interno del servidor."}), 500

    @itinerario_bp.delete("/<string:id>")
    @jwt_required()
    def eliminar(id):
        """
        Elimina lógicamente un itinerario (soft delete).
        ---
        tags:
          - Itinerarios
        security:
          - Bearer: []
        parameters:
          - name: id
            in: path
            type: string
            required: true
            description: ID UUID del itinerario
            example: 550e8400-e29b-41d4-a716-446655440000
        responses:
          200:
            description: Itinerario eliminado correctamente
            schema:
              type: object
              properties:
                mensaje:
                  type: string
                  example: Itinerario eliminado correctamente.
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Itinerario no encontrado
            schema:
              $ref: '#/definitions/Error'
          500:
            description: Error interno del servidor
            schema:
              $ref: '#/definitions/Error'
        """
        usuario_id = get_jwt_identity()
        try:
            itinerario_service.eliminar(id, usuario_id)
            return jsonify({"mensaje": "Itinerario eliminado correctamente."}), 200
        except ItinerarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404
        except Exception:
            return jsonify({"error": "Error interno del servidor."}), 500

    return itinerario_bp
