from dependency_injector import containers, providers
from app.domain.interfaces import IBrokerConsumer
from app.domain.interfaces.IScraper import IScraper
from app.domain.interfaces.IDatabase import IDatabase
from app.domain.interfaces.IScraperService import IScraperService
from app.config.config import Settings
from app.infrastructure.database.OracleDB import OracleDB
from app.application.services.ScraperService import ScraperService
from app.infrastructure.filesystem.TempWorkspace import TempWorkspace
from app.infrastructure.rabbitmq.RabbitMQConsumer import RabbitMQConsumer
from app.domain.interfaces.IS3Manager import IS3Manager
from app.infrastructure.s3.S3Manager import S3Manager
from app.infrastructure.database.repositories.ControlAutosRep import ControlAutosRep
from app.domain.interfaces.IGetDataService import IGetDataService
from app.application.services.GetDataService import GetDataService
from app.application.services.CEJScraper import CEJScraper
from app.infrastructure.database.repositories.DatosRamaRep import DatosRamaRep
from app.domain.interfaces.IInsertDataService import IInsertDataService
from app.application.services.InsertDataService import InsertDataService
from app.domain.interfaces.IProcessDataService import IProcessDataService
from app.application.services.ProcessDataService import ProcessDataService
from app.domain.interfaces.IBrowserManager import IBrowserManager
from app.infrastructure.browserManager.BrowserManager import BrowserManager
from app.application.services.bot.FormScraper import FormScraper
from app.domain.interfaces.IFormScraper import IFormScraper
from app.infrastructure.database.repositories.ActorsRamaRep import ActorsRamaRep
from app.application.services.factories.ProcessorFactory import ProcessorFactory
from app.domain.interfaces.IProcessorFactory import IProcessorFactory
from app.infrastructure.downloaders.DownloadHelper import DownloadHelper
from app.infrastructure.downloaders.DocxProcessor import DocxProcessor
from app.domain.interfaces.IDownloadHelper import IDownloadHelper
from app.domain.interfaces.IFileProcessor import IFileProcessor
from app.infrastructure.downloaders.PdfProcessor import PdfProcessor

class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)
    wiring_config = containers.WiringConfiguration(
        modules=["main"]
    )


    # Provider manager de browser
    browserManager : providers.Singleton[IBrowserManager] = providers.Singleton(
        BrowserManager,
        proxy= settings.provided.proxySet.proxy
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
    
    # Provider del consumidor
    consumer: providers.Singleton[IBrokerConsumer] = providers.Singleton(
        RabbitMQConsumer,
        host=settings.provided.rabbitmq.host,
        port = settings.provided.rabbitmq.port,
        queueName = settings.provided.rabbitmq.subQueueName,
        prefetchCount = settings.provided.rabbitmq.prefetchCount,
    )
    

    
    # Provider del S3
    s3Manager : providers.Singleton[IS3Manager] = providers.Singleton(
        S3Manager,
        awsAccessKey = settings.provided.s3.awsAccessKey,
        awsSecretKey = settings.provided.s3.awsSecretKey,
        bucketName = settings.provided.s3.bucketLitigando,
        s3Prefix = settings.provided.s3.prefixLitigando,
      
    )

    docxProcessor: providers.Factory[IFileProcessor] = providers.Factory(
        DocxProcessor,

    )
    

        #Provider de procesadores
    pdfProcessor: providers.Factory[IFileProcessor] = providers.Factory(
        PdfProcessor,

    )
    
    processorFactory: providers.Factory[IProcessorFactory] = providers.Factory(
        ProcessorFactory,
        processorMap={
            # PDF
            "application/pdf": pdfProcessor,

            # Word moderno (.docx)
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": docxProcessor,
            # Word antiguo (.doc)
            "application/msword": docxProcessor,

            "application/octet-stream": docxProcessor,
        }
    )

    

    
    # Filesystem 
    tempWorkspace = providers.Singleton(
        TempWorkspace,
        basePath = settings.provided.file.tempFolder
    )

    datosRamaRep = providers.Factory(
        DatosRamaRep,
        table= settings.provided.db.TB_DATOS_PROCESO_RAMA
       
    )

    controlAutosRep = providers.Factory(
        ControlAutosRep,
        table= settings.provided.db.TB_CONTROL_AUTOS_RAMA
    )

    actorsRamaRep =  providers.Factory(
        ActorsRamaRep,
        table= settings.provided.db.TB_ACTORES_RAMA
    )

    getDataService: providers.Factory[IGetDataService] = providers.Factory(
        GetDataService,
    )


    getDataService: providers.Factory[IGetDataService] = providers.Factory(
        GetDataService,
    )


    downloadHelper: providers.Factory[IDownloadHelper] = providers.Factory(
        DownloadHelper,
 
    )


    insertDataService: providers.Factory[IInsertDataService] = providers.Factory(
        InsertDataService,
        s3Manager= s3Manager,
        controlAutosRep = controlAutosRep,
        datosRamaRep=datosRamaRep,
        actorsRamaRep = actorsRamaRep
        
    )

    processDataService: providers.Factory[IProcessDataService] = providers.Factory(
        ProcessDataService,
        insertDataService =  insertDataService,
        downloadHelper = downloadHelper,
        processorFactory = processorFactory,
       
    )

    formScraper : providers.Factory[IFormScraper] = providers.Factory(
        FormScraper,
    )



    cejScraper: providers.Factory[IScraper] = providers.Factory(
        CEJScraper,
        getData = getDataService,
        insertDataService = insertDataService,
        processData = processDataService,
        url=settings.provided.browser.url,
        formScraper = formScraper,
        tempWorkspace = tempWorkspace

        
    )

    scraperService:providers.Factory[IScraperService] = providers.Factory(
        ScraperService,
        db = db,
        tempWorkspace = tempWorkspace,
        cejScraper=cejScraper,
        browserManager = browserManager,
        
    
    )
