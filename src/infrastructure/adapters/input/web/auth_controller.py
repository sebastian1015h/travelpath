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
        """
        Registra un nuevo usuario en el sistema.
        ---
        tags:
          - Autenticación
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - nombre
                - correo
                - contrasena
              properties:
                nombre:
                  type: string
                  example: Juan Pérez
                correo:
                  type: string
                  example: juan@example.com
                contrasena:
                  type: string
                  example: MiContraseña123
        responses:
          201:
            description: Usuario registrado exitosamente
            schema:
              type: object
              properties:
                mensaje:
                  type: string
                  example: Registro exitoso.
                usuario:
                  $ref: '#/definitions/Usuario'
          400:
            description: Campos requeridos faltantes
            schema:
              $ref: '#/definitions/Error'
          409:
            description: El correo ya está registrado
            schema:
              $ref: '#/definitions/Error'
          500:
            description: Error interno del servidor
            schema:
              $ref: '#/definitions/Error'
        definitions:
          Usuario:
            type: object
            properties:
              id:
                type: string
                example: 550e8400-e29b-41d4-a716-446655440000
              nombre:
                type: string
                example: Juan Pérez
              correo:
                type: string
                example: juan@example.com
          Error:
            type: object
            properties:
              error:
                type: string
                example: Mensaje de error
        """
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
        """
        Autentica un usuario y retorna tokens JWT.
        ---
        tags:
          - Autenticación
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - correo
                - contrasena
              properties:
                correo:
                  type: string
                  example: juan@example.com
                contrasena:
                  type: string
                  example: MiContraseña123
                recordar:
                  type: boolean
                  example: false
                  description: Si es true, el access token dura 30 días en vez de 24 horas
        responses:
          200:
            description: Login exitoso, retorna tokens JWT
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                refresh_token:
                  type: string
                  example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                usuario:
                  $ref: '#/definitions/Usuario'
          400:
            description: Campos requeridos faltantes
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Credenciales inválidas
            schema:
              $ref: '#/definitions/Error'
          500:
            description: Error interno del servidor
            schema:
              $ref: '#/definitions/Error'
        """
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
        """
        Cierra la sesión revocando el token JWT actual.
        ---
        tags:
          - Autenticación
        security:
          - Bearer: []
        responses:
          200:
            description: Sesión cerrada correctamente
            schema:
              type: object
              properties:
                mensaje:
                  type: string
                  example: Sesión cerrada correctamente.
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
        """
        jti = get_jwt().get("jti")
        auth_service.logout(jti)
        return jsonify({"mensaje": "Sesión cerrada correctamente."}), 200

    @auth_bp.post("/refresh")
    @jwt_required(refresh=True)
    def refresh():
        """
        Renueva el access token usando el refresh token.
        ---
        tags:
          - Autenticación
        security:
          - Bearer: []
        responses:
          200:
            description: Nuevo access token generado
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
          401:
            description: Refresh token inválido o expirado
            schema:
              $ref: '#/definitions/Error'
        """
        from flask_jwt_extended import create_access_token
        usuario_id = get_jwt_identity()
        new_token = create_access_token(identity=usuario_id)
        return jsonify({"access_token": new_token}), 200

    @auth_bp.post("/recuperar-contrasena")
    def recuperar_contrasena():
        """
        Solicita recuperación de contraseña para un correo registrado.
        ---
        tags:
          - Autenticación
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - correo
              properties:
                correo:
                  type: string
                  example: juan@example.com
        responses:
          200:
            description: Respuesta genérica (no revela si el correo existe)
            schema:
              type: object
              properties:
                mensaje:
                  type: string
                  example: Si el correo existe, recibirás instrucciones.
          400:
            description: Correo no proporcionado
            schema:
              $ref: '#/definitions/Error'
        """
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
        """
        Retorna el perfil del usuario autenticado.
        ---
        tags:
          - Autenticación
        security:
          - Bearer: []
        responses:
          200:
            description: Datos del usuario autenticado
            schema:
              $ref: '#/definitions/Usuario'
          401:
            description: Token inválido o no proporcionado
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Usuario no encontrado
            schema:
              $ref: '#/definitions/Error'
        """
        usuario_id = get_jwt_identity()
        try:
            usuario = auth_service.obtener_por_id(usuario_id)
            return jsonify(usuario.to_dict()), 200
        except UsuarioNoEncontradoException as e:
            return jsonify({"error": str(e)}), 404

    return auth_bp
