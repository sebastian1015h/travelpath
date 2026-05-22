from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(
        default="sqlite:///travelpath.db",
        alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(default="cambia_esto_en_produccion", alias="JWT_SECRET_KEY")
    flask_debug: bool = Field(default=True, alias="FLASK_DEBUG")
    frontend_origin: str = Field(default="*", alias="FRONTEND_ORIGIN")
<<<<<<< HEAD
=======
    airport_service_url: str = Field(default="http://localhost:8001", alias="AIRPORT_SERVICE_URL")
>>>>>>> origin/master

    model_config = {"env_file": ".env", "populate_by_name": True}


settings = Settings()
