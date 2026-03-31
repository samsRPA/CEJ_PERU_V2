import logging

from fastapi import FastAPI

from contextlib import asynccontextmanager

from app.api.views import getApiRouter
from app.config.config import loadConfig
from app.dependencies.Dependencies import Dependencies

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = loadConfig()
    dependency = Dependencies()
    dependency.settings.override(config) 

    app.container = dependency

    db = dependency.db()
    producer = dependency.rabbitmqProducer()
    try:
        await producer.connect()
        await db.connect()
        yield  # Aquí se ejecuta la app
    except Exception as e:
        logging.exception("🔴 Error durante la ejecución principal", exc_info=e)
    finally:
        try:
            await producer.close()
        except Exception as e:
            logging.warning(f"🟡 No se pudo cerrar RabbitMQ correctamente: {e}")
        try:
            if db.isConnected:
                await db.closeConnection()
        except Exception as e:
            logging.warning(f"🟡 No se pudo cerrar la DB correctamente: {e}")

app = FastAPI(
    lifespan=lifespan,
    title="ms_CEJ_PERU API Service",
    description=(
        "ms_watcher_CEJapp"
    ),
    version="3.0.0",
    contact={
        "name": "Rpa Litigando Department",
        "email": "samuel.monsalve@litigando.com",
    },
    openapi_url="/api/v3/openapi.json", 
    docs_url="/api/v3/swagger",  
    redoc_url="/api/v3/redocs",
)
app.include_router(getApiRouter())

@app.get("/")
def default():
    return {"mensaje": "Hello ms_watcher_CEJ"}
            