from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
<<<<<<< HEAD
=======
from flasgger import Swagger
>>>>>>> origin/master

from src.infrastructure.config.settings import settings
from src.infrastructure.config.database import get_db_session, init_db, remove_db_session
from src.infrastructure.security.jwt_handler import init_jwt

from src.infrastructure.adapters.output.persistence.sqlalchemy_usuario_repo import SQLAlchemyUsuarioRepo
from src.infrastructure.adapters.output.persistence.sqlalchemy_itinerario_repo import SQLAlchemyItinerarioRepo
<<<<<<< HEAD
from src.infrastructure.adapters.output.external.api_colombia_adapter import ApiColombiaAdapter
=======
from src.infrastructure.adapters.output.external.airport_service_http_adapter import AirportServiceHttpAdapter
>>>>>>> origin/master

from src.application.services.auth_service import AuthService
from src.application.services.itinerario_service import ItinerarioService
from src.application.services.token_blacklist_service import TokenBlacklistService

from src.infrastructure.adapters.input.web.auth_controller import create_auth_blueprint
from src.infrastructure.adapters.input.web.itinerario_controller import create_itinerario_blueprint
from src.infrastructure.adapters.input.web.aeropuerto_controller import create_aeropuerto_blueprint


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../../presentation/templates",
        static_folder="../../presentation/static",
    )

    app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
    app.config["SECRET_KEY"]     = settings.jwt_secret_key
    app.config["DEBUG"]          = settings.flask_debug

<<<<<<< HEAD
=======
    Swagger(app, template={
        "info": {
            "title": "Itinerary Service API",
            "description": (
                "Microservicio de gestión de itinerarios de viaje. "
                "Maneja autenticación JWT, CRUD de itinerarios y consulta "
                "de aeropuertos delegando al Airport Service."
            ),
            "version": "1.0.0",
            "contact": {"name": "TravelPath Team"},
        },
        "host": "localhost:5000",
        "basePath": "/",
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT token. Formato: Bearer <token>",
            }
        },
    })

>>>>>>> origin/master
    origins = settings.frontend_origin
    CORS(app, resources={r"/api/*": {"origins": origins}, r"/auth/*": {"origins": origins}})

    jwt: JWTManager = init_jwt(app)

    db_session     = get_db_session()
    token_blacklist = TokenBlacklistService(db_session)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_header, payload):
        return token_blacklist.esta_revocado(payload.get("jti", ""))

    @jwt.revoked_token_loader
    def revoked_token_callback(_header, _payload):
        from flask import jsonify
        return jsonify({"error": "Token revocado. Inicia sesión nuevamente."}), 401

    @jwt.expired_token_loader
    def expired_token_callback(_header, _payload):
        from flask import jsonify
        return jsonify({"error": "Token expirado. Inicia sesión nuevamente."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(_error):
        from flask import jsonify
        return jsonify({"error": "Token de autenticación requerido."}), 401

    init_db()

    usuario_repo    = SQLAlchemyUsuarioRepo(db_session)
    itinerario_repo = SQLAlchemyItinerarioRepo(db_session)
<<<<<<< HEAD
    aeropuerto_client = ApiColombiaAdapter()
=======
    aeropuerto_client = AirportServiceHttpAdapter(settings.airport_service_url)
>>>>>>> origin/master

    auth_service       = AuthService(usuario_repo, token_blacklist)
    itinerario_service = ItinerarioService(itinerario_repo, aeropuerto_client)

    app.register_blueprint(create_auth_blueprint(auth_service))
    app.register_blueprint(create_itinerario_blueprint(itinerario_service))
    app.register_blueprint(create_aeropuerto_blueprint(aeropuerto_client))

    _register_frontend_routes(app)

    @app.get("/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok"}), 200

    @app.teardown_appcontext
    def cleanup_session(*_):
        remove_db_session()

    return app


def _register_frontend_routes(app: Flask):
    from flask import render_template, redirect, url_for

    @app.get("/")
    def index():
        return redirect(url_for("frontend_login"))

    @app.get("/login")
    def frontend_login():
        return render_template("auth/login.html")

    @app.get("/register")
    def frontend_register():
        return render_template("auth/register.html")

    @app.get("/itinerarios")
    def frontend_lista():
        return render_template("itinerarios/lista.html")

    @app.get("/itinerarios/nuevo")
    def frontend_nuevo():
        return render_template("itinerarios/formulario.html")

    @app.get("/itinerarios/<string:id>/editar")
    def frontend_editar(id):
        return render_template("itinerarios/formulario.html", itinerario_id=id)

    @app.get("/itinerarios/<string:id>")
    def frontend_detalle(id):
        return render_template("itinerarios/detalle.html", itinerario_id=id)
