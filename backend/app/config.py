import re
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./dev.db"

    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"

    jwt_secret: str = "cambia-este-secreto"
    jwt_expire_hours: int = 12

    admin_email: str = ""
    admin_password: str = ""
    admin_name: str = "Administrador"

    cors_origins: str = "http://localhost:5173"
    cookie_secure: bool = False

    @property
    def sqlalchemy_url(self) -> str:
        """DATABASE_URL as given by hosting providers, adapted for asyncpg."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        # Any other Postgres driver in the URL (psycopg, psycopg2) is swapped for asyncpg.
        url = re.sub(r"^postgresql(\+\w+)?://", "postgresql+asyncpg://", url)
        if not url.startswith("postgresql+asyncpg://"):
            return url

        # asyncpg does not understand libpq's sslmode / channel_binding.
        parts = urlsplit(url)
        query = []
        for key, value in parse_qsl(parts.query):
            if key == "sslmode":
                if value != "disable":
                    query.append(("ssl", "require"))
            elif key != "channel_binding":
                query.append((key, value))
        return urlunsplit(parts._replace(query=urlencode(query)))

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
