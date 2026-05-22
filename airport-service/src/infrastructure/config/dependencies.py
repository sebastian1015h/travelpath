from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from src.infrastructure.adapters.output.external.api_colombia_adapter import ApiColombiaAdapter
from src.application.services.aeropuerto_service import AeropuertoService
from src.infrastructure.adapters.input.web.aeropuerto_controller import create_aeropuerto_blueprint

SWAGGER_TEMPLATE = {
    "info": {
        "title": "Airport Service API",
        "description": (
            "Microservicio de consulta de aeropuertos. "
            "Consume API Colombia y AirportGap para exponer información "
            "de aeropuertos en formato unificado."
        ),
        "version": "1.0.0",
        "contact": {"name": "TravelPath Team"},
    },
    "host": "localhost:8001",
    "basePath": "/",
}


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    Swagger(app, template=SWAGGER_TEMPLATE)

    adapter = ApiColombiaAdapter()
    service = AeropuertoService(adapter)

    app.register_blueprint(create_aeropuerto_blueprint(service))

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "airport-service"}, 200

    return app
