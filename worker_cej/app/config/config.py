from pathlib import Path
from pydantic import Field

from app.config.base import EnvConfig

class RabbitMQSettings(EnvConfig):
    host: str = Field(..., alias="RABBITMQ_HOST")
    port: int = Field(..., alias="RABBITMQ_PORT")
    subQueueName: str = Field(..., alias="SUB_QUEUE_NAME")
    prefetchCount: int = Field(..., alias="PREFETCH_COUNT")

class DatabaseSettings(EnvConfig):
    user: str = Field(..., alias="DB_USERNAME")
    password: str = Field(..., alias="DB_PASSWORD")
    host: str = Field(..., alias="DB_HOST")
    port: str = Field(..., alias="DB_PORT")
    dbName: str = Field(..., alias="DB_NAME")

    #  🔹 Tablas 
    TB_CONTROL_AUTOS_RAMA : str = Field(..., alias='TB_CONTROL_AUTOS_RAMA')
    TB_DATOS_PROCESO_RAMA : str = Field(..., alias='TB_DATOS_PROCESO_RAMA')
    TB_ACTORES_RAMA  : str = Field(..., alias='TB_ACTORES_RAMA')


class FileSettings(EnvConfig): 
    tempFolder: Path  = Field(..., alias="FOLDER")

class S3ManagerSettings(EnvConfig):
    awsAccessKey: str = Field(..., alias="S3_ACCESS_KEY")
    awsSecretKey: str = Field(..., alias="S3_SECRET")
    # Litigando
    bucketLitigando: str = Field(..., alias="S3_BUCKET_LITIGANDO")
    prefixLitigando: str = Field(..., alias="S3_PREFIX_LITIGANDO")
  
class ProxySetting(EnvConfig):
    proxy: str = Field(..., alias="PROXY")
  
class BrowserSetting(EnvConfig):
    url: str = Field(..., alias="URL")

class Settings(EnvConfig):
    file: FileSettings = FileSettings()
    db: DatabaseSettings = DatabaseSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    s3 : S3ManagerSettings = S3ManagerSettings()
    proxySet: ProxySetting = ProxySetting()
    browser : BrowserSetting = BrowserSetting()
    
def loadConfig() -> Settings:
    return Settings()