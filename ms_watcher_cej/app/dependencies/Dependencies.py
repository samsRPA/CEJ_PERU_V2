from dependency_injector import containers, providers

from app.domain.interfaces.IDatabase import IDatabase
from app.domain.interfaces.IBrokerProducer import IBrokerProducer


from app.config.config import Settings
from app.infrastructure.database.OracleDB import OracleDB

from app.infrastructure.rabbitmq.RabbitMQProducer import RabbitMQProducer

from app.application.services.CEJPeruService import CEJPeruService
from app.infrastructure.database.repositories.CEJRep import CEJRep
from app.domain.interfaces.ICEJPeruService import ICEJPeruService


class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)
    wiring_config = containers.WiringConfiguration(
        modules=["app.api.routes.CEJPeruRoutes"]
    )
    
    #Provider de db
    db: providers.Singleton[IDatabase] = providers.Singleton(
        OracleDB,
        user = settings.provided.db.user,
        password = settings.provided.db.password,
        host = settings.provided.db.host,
        port = settings.provided.db.port,
        dbName = settings.provided.db.dbName,
    )
    
    #Provide de Repostories
    cejRep = providers.Factory(
       CEJRep ,

    )
    
    # Provider del productor
    rabbitmqProducer: providers.Singleton[IBrokerProducer] = providers.Singleton(
        RabbitMQProducer,
        host=settings.provided.rabbitmq.host, 
        port = settings.provided.rabbitmq.port, 
        queueName=settings.provided.rabbitmq.queue_name
    )
    
    # Servicio principal
    cejPeruService: providers.Factory[ICEJPeruService] = providers.Factory(
        CEJPeruService,
        db = db,
        cejRep = cejRep  ,
        producer = rabbitmqProducer
    )
    