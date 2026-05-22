from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta


def init_jwt(app: Flask) -> JWTManager:
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    jwt = JWTManager(app)
    return jwt
