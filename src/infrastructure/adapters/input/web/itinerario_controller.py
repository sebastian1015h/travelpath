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
        usuario_id = get_jwt_identity()
        itinerarios = itinerario_service.listar_por_usuario(usuario_id)
        return jsonify([i.to_dict() for i in itinerarios]), 200

    @itinerario_bp.post("")
    @jwt_required()
    def crear():
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
        usuario_id = get_jwt_identity()
        return jsonify(itinerario_service.historial_por_anio(usuario_id)), 200

    @itinerario_bp.get("/<string:id>")
    @jwt_required()
    def detalle(id):
        usuario_id = get_jwt_identity()
        try:
            resultado = itinerario_service.obtener_detalle(id, usuario_id)
            return jsonify(resultado.to_dict()), 200
        except ItinerarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404

    @itinerario_bp.put("/<string:id>")
    @jwt_required()
    def modificar(id):
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
        usuario_id = get_jwt_identity()
        try:
            itinerario_service.eliminar(id, usuario_id)
            return jsonify({"mensaje": "Itinerario eliminado correctamente."}), 200
        except ItinerarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404
        except Exception:
            return jsonify({"error": "Error interno del servidor."}), 500

    return itinerario_bp
