from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(
        default="sqlite:///travelpath.db",
        alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(default="cambia_esto_en_produccion", alias="JWT_SECRET_KEY")
    jwt_access_token_expires: int = Field(default=86400, alias="JWT_ACCESS_TOKEN_EXPIRES")
    api_colombia_base_url: str = Field(
        default="https://api-colombia.com/api/v1", alias="API_COLOMBIA_BASE_URL"
    )
    flask_env: str = Field(default="development", alias="FLASK_ENV")
    flask_debug: bool = Field(default=True, alias="FLASK_DEBUG")

    model_config = {"env_file": ".env", "populate_by_name": True}


settings = Settings()
