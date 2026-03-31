import asyncio
from datetime import datetime
import json
import logging

from bs4 import BeautifulSoup
from app.domain.interfaces.IScraper import IScraper
from app.domain.interfaces.IGetDataService import IGetDataService
from app.domain.interfaces.IInsertDataService import IInsertDataService
from app.application.services.ProcessDataService import ProcessDataService
from app.infrastructure.filesystem.TempWorkspace import TempWorkspace
from app.application.dto.AutosRequestDto import AutosRequestDto
from app.application.dto.BotReq import BotReq
from pydoll.browser.tab import Tab
from app.domain.interfaces.IFormScraper import IFormScraper
from app.application.dto.exception.BlockedByBotManagerError import BlockedByBotManagerError
class CEJScraper(IScraper):

    def __init__(self, getData:IGetDataService, insertDataService:IInsertDataService, processData: ProcessDataService, url:str, formScraper: IFormScraper, tempWorkspace:TempWorkspace):
        self.getData= getData
        self.insertDataService= insertDataService
        self.processData= processData
        self.url = url
        self.formScraper = formScraper
        self.tempWorkspace = tempWorkspace
        self.logger = logging.getLogger(__name__)


    async def scraping( self, data: BotReq, conn, outputDir, tab:Tab):
        try:
  

            
            radicado = data.radicado
            self.logger.info(f"🌐 Iniciando scraping CEJ con radicado : {radicado}")
            await tab.go_to(self.url)

            if await self._isBlocked(tab):
                self.logger.warning("🚫 IP bloqueada por Radware. Reiniciando navegador...")
                raise BlockedByBotManagerError("Radware block detected")

            isFormCompleted = await self.formScraper.fillOutForm(tab, data)

            if not isFormCompleted:
                self.logger.warning("⚠️ No se logro llenar el formulario completo.")
                return False
            
            # Extraer el HTML puro
            pureHTML = await self.formScraper.getHtml(tab)
            
            if not pureHTML:
                return False
            
            soup = BeautifulSoup(pureHTML, "html.parser")

            with open(f"/app/temp/index_{radicado}.html", "w", encoding="utf-8") as f:
                 f.write(pureHTML)
            self.logger.info("HTML GUARDADO")
            
            caseReport, courtOfficeCode2 = self.getData.getCaseReport(soup,radicado)

            # if actorsRama :
            #     await self.processData.processCaseReport(conn,radicado,caseReport)

            
            # actorsRama = self.getData.getActoresRama(soup,radicado)

            # if actorsRama:
            #     await self.processData.processActorsRama(conn,radicado,actorsRama)
            
            actions, downloadableActions =  self.getData.getActions(soup,radicado,courtOfficeCode2)

            await self.tempWorkspace.appendNDJson("jsons","actuaciones", actions)
            # ✅ Filtrar ANTES de descargar (rápido, solo BD)
            newActions = await self.processData.filterNewActions(conn, radicado, downloadableActions)

            if not newActions:
                self.logger.info(f"✅ No hay actuaciones nuevas para descargar → radicado {radicado}")
                self._logFinalScrapper(radicado)
                return 

            await self.processData.processActions(conn,radicado,newActions, outputDir, tab)
            #await self.tempWorkspace.appendNDJson("jsons","downloadable", downloadableActions )

            # # Guardar como archivo HTML
      
            # await tab.take_screenshot(f"/app/temp/captura_{radicado}.png")
            
            self._logFinalScrapper(radicado)
  
        except Exception as e:
            self.logger.exception(f"🔴 Error al procesar el scraper CEJ PERU {e}")
            raise e



    async def _isBlocked(self, tab: Tab) -> bool:
        """Detecta si la página fue bloqueada por Radware Bot Manager."""
        try:
            htmlResponse = await tab.execute_script("return document.documentElement.outerHTML;")
            html = htmlResponse["result"]["result"]["value"]
            return (
                "eres un bot" in html
            )
        except Exception:
            self.logger.warning("⚠️ No se pudo verificar bloqueo de Radware.")
            return False

            
    def _logFinalScrapper(self,radicado):
        self.logger.info(f"🎯 Scraper Finalizado para el radicado {radicado} | Fecha y hora del recorrido: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        
    