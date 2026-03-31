import json
import logging
from app.application.dto.BotReq import BotReq
from app.domain.interfaces.IDatabase import IDatabase
from app.domain.interfaces.IScraperService import IScraperService
from app.infrastructure.filesystem.TempWorkspace import TempWorkspace
from app.domain.interfaces.IScraper import IScraper
from app.domain.interfaces.IBrowserManager import IBrowserManager
from app.application.dto.exception.BlockedByBotManagerError import BlockedByBotManagerError

class ScraperService(IScraperService):
    def __init__(self, db: IDatabase, tempWorkspace:TempWorkspace, cejScraper:IScraper, browserManager : IBrowserManager ):
        self.db = db
        self.tempWorkspace = tempWorkspace
        self.cejScraper=cejScraper
        self.browserManager = browserManager
        self.logger = logging.getLogger(__name__)
    
    def _parseMessage(self, body: bytes) -> BotReq:
        raw = json.loads(body.decode("utf-8"))
        return BotReq.fromRaw(raw)
    
    async def _process(self, data: BotReq, outputDir):
        conn = None
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                tab = await self.browserManager.getBrowser()
                conn = await self.db.acquireConnection()
                await self.browserManager.setDownloadDirectory(str(outputDir))
                await self.cejScraper.scraping(data, conn, outputDir, tab)
                await self.db.commit(conn)
                return  # ✅ Éxito, salir del loop

            except BlockedByBotManagerError:
                self.logger.warning(
                    f"🔄 Intento {attempt}/{max_retries}: IP bloqueada. "
                    "Reiniciando navegador..."
                )
                await self.browserManager.restart()

                if attempt == max_retries:
                    self.logger.error("🔴 Se agotaron los reintentos por bloqueo de IP.")
                    raise

            except Exception:
                self.logger.exception("🔴 Error al procesar el scraper")
                raise

            finally:
                if conn:
                    try:
                        await self.db.releaseConnection(conn)
                    except Exception as e:
                        self.logger.warning(f"Error liberando conexión DB: {e}")
                conn = None  # reset para el siguiente intento

    async def handleMessage(self, body: bytes):
        try:
            data = self._parseMessage(body)

            with self.tempWorkspace.useTempFolder(data.folderName) as outputDir:
                await self._process(data, outputDir)

        except KeyError as e:
            self.logger.error(f"🔴 Configuración inválida: {e}")
            raise

        except json.JSONDecodeError:
            self.logger.error("🔴 Mensaje inválido: JSON malformado")
            raise

        except Exception:
            self.logger.exception("🔴 Error procesando mensaje")
            raise


  