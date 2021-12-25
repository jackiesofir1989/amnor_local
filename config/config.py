from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field(default='postgresql+asyncpg://fastapi_traefik:fastapi_traefik@localhost:5432/fastapi_traefik', env='DATABASE_URL')
    system_path: str = Field(default='config/system_layout_config', env='SYSTEM_PATH')
    tz: str = Field(default='Asia/Jerusalem', env='TZ')
    # datetime.now(tz=pytz.timezone(tz))


settings = Settings()
