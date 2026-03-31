import os
from pathlib import Path
import signal
import logging
import asyncio
import sys

from app.config.config import loadConfig
from app.dependencies.Dependencies import Dependencies

def setup_logger(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)

    container_name = os.getenv("HOSTNAME", "unknown-container")

    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - %(levelname)s - [%(module)s] - [Container {container_name}] %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
logger = logging.getLogger(__name__)
logging.getLogger("pydoll").setLevel(logging.CRITICAL)

def setupSignalHandlers(stopEvent: asyncio.Event):
    loop = asyncio.get_running_loop()

    def handleSignal():
        stopEvent.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handleSignal)


async def run():
    consumerTask = None
    config = loadConfig()

    # Crear el path del log
    log_path = Path("/app/temp/logs/logs.csv")

    # Inicializar logger
    setup_logger(log_path)

    dependency = Dependencies()
    dependency.settings.override(config)

    # Resolver dependencias
    db = dependency.db()
    consumer = dependency.consumer()
    scraperService = dependency.scraperService()
    browser= dependency.browserManager()
    # Registrar el callback 
    consumer.onMessage(scraperService.handleMessage)

    stopEvent = asyncio.Event()
    setupSignalHandlers(stopEvent)

    try:
        await db.connect()
        await browser.start()
  
        # Arrancar el consumer
        consumerTask = asyncio.create_task(
            consumer.startConsuming()
        )

        await stopEvent.wait()

    except Exception as e:
        logger.exception(f"🔴 Error durante la ejecución principal {e}")

    finally:
        
        if consumerTask:
            consumerTask.cancel()
        if browser.isStarted:
                await browser.close()
        try:
            if db.isConnected:
                await db.closeConnection()

            logger.info("🔌 Todos los recursos cerrados correctamente.")
        except Exception as e:
            logger.warning(f"🔴 Error al cerrar recursos: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("👋 Señal de interrupción detectada (CTRL+C o kill).")
