from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from src.application.services.auth_service import AuthService
from src.application.dtos.usuario_dto import RegisterDTO, LoginDTO
from src.domain.exceptions.domain_exceptions import (
    EmailYaRegistradoException,
    CredencialesInvalidasException,
    UsuarioNoEncontradoException,
)


def create_auth_blueprint(auth_service: AuthService) -> Blueprint:
    auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

    @auth_bp.post("/register")
    def register():
        body = request.get_json(silent=True) or {}
        nombre = body.get("nombre", "").strip()
        correo = body.get("correo", "").strip()
        contrasena = body.get("contrasena", "")

        if not nombre or not correo or not contrasena:
            return jsonify({"error": "Nombre, correo y contraseña son requeridos."}), 400

        try:
            dto = RegisterDTO(nombre=nombre, correo=correo, contrasena=contrasena)
            usuario = auth_service.registrar(dto)
            return jsonify({"mensaje": "Registro exitoso.", "usuario": usuario.to_dict()}), 201
        except EmailYaRegistradoException as e:
            return jsonify({"error": str(e)}), 409
        except Exception:
            return jsonify({"error": "Error interno del servidor."}), 500

    @auth_bp.post("/login")
    def login():
        body = request.get_json(silent=True) or {}
        correo = body.get("correo", "").strip()
        contrasena = body.get("contrasena", "")
        recordar = body.get("recordar", False)

        if not correo or not contrasena:
            return jsonify({"error": "Correo y contraseña son requeridos."}), 400

        try:
            dto = LoginDTO(correo=correo, contrasena=contrasena, recordar=recordar)
            resultado = auth_service.login(dto)
            return jsonify(resultado), 200
        except CredencialesInvalidasException as e:
            return jsonify({"error": str(e)}), 401
        except Exception:
            return jsonify({"error": "Error interno del servidor."}), 500

    @auth_bp.post("/logout")
    @jwt_required()
    def logout():
        jti = get_jwt().get("jti")
        auth_service.logout(jti)
        return jsonify({"mensaje": "Sesión cerrada correctamente."}), 200

    @auth_bp.post("/refresh")
    @jwt_required(refresh=True)
    def refresh():
        from flask_jwt_extended import create_access_token
        usuario_id = get_jwt_identity()
        new_token = create_access_token(identity=usuario_id)
        return jsonify({"access_token": new_token}), 200

    @auth_bp.post("/recuperar-contrasena")
    def recuperar_contrasena():
        body = request.get_json(silent=True) or {}
        correo = body.get("correo", "").strip()
        if not correo:
            return jsonify({"error": "El correo es requerido."}), 400
        try:
            auth_service.recuperar_contrasena(correo)
            return jsonify({"mensaje": "Si el correo existe, recibirás instrucciones."}), 200
        except UsuarioNoEncontradoException:
            return jsonify({"mensaje": "Si el correo existe, recibirás instrucciones."}), 200

    @auth_bp.get("/me")
    @jwt_required()
    def me():
        usuario_id = get_jwt_identity()
        try:
            usuario = auth_service.obtener_por_id(usuario_id)
            return jsonify(usuario.to_dict()), 200
        except UsuarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404

    return auth_bp
