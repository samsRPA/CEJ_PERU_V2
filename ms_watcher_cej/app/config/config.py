from pydantic import Field

from app.config.base import EnvConfig
from pydantic_settings import BaseSettings

class RabbitMQSettings(EnvConfig):
    host: str = Field(..., alias="RABBITMQ_HOST")
    port: int = Field(..., alias="RABBITMQ_PORT")
    queue_name: str = Field(..., alias="PUB_QUEUE_NAME")

class DatabaseSettings(EnvConfig):
    user: str = Field(..., alias="DB_USERNAME")
    password: str = Field(..., alias="DB_PASSWORD")
    host: str = Field(..., alias="DB_HOST")
    port: str = Field(..., alias="DB_PORT")
    dbName: str = Field(..., alias="DB_NAME")

# class dbTablesSettings(EnvConfig):
#     courtTb: str = Field(..., alias="DESPACHOS")
#     localityTb: str = Field(..., alias="LOCALIDADES")
 
class Settings(BaseSettings):
    db: DatabaseSettings = DatabaseSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    #dbTables: dbTablesSettings = dbTablesSettings()

def loadConfig() -> Settings:
    return Settings()