from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    PORT: int = 22222
    WORKERS: int = 2
    WORKSPACE: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "dc_svc.log"
    JSON_LOGS: bool = False

    class Config:
        env_prefix = "DC_SVC_"
        case_sensitive = True


config = Settings()
