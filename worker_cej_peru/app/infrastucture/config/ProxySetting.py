from pydantic import Field
from app.infrastucture.config.EnvConfig import EnvConfig


class ProxySetting(EnvConfig):
    proxy: str = Field(..., alias="PROXY")
