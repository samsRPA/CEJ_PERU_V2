import logging
import os
from app.domain.interfaces.IProcessDataService import IProcessDataService
from app.infrastructure.filesystem.TempWorkspace import TempWorkspace
from app.infrastructure.database.repositories.ControlAutosRep import ControlAutosRep
from app.domain.interfaces.IInsertDataService import IInsertDataService
from pydoll.browser.tab import Tab
from app.domain.interfaces.IDownloadHelper import IDownloadHelper
from app.domain.interfaces.IProcessorFactory import IProcessorFactory
from datetime import date, datetime

class ProcessDataService(IProcessDataService):
    
    def __init__(self, insertDataService: IInsertDataService  , downloadHelper = IDownloadHelper, processorFactory = IProcessorFactory):
        self.insertDataService= insertDataService
        self.downloadHelper = downloadHelper
        self.processorFactory = processorFactory
        self.logger= logging.getLogger(__name__)
       
    async def processCaseReport(self, conn, radicado, caseReport):
        try:

            for  dataName, dataValue in caseReport.items():

                    # ⚠️ Omitir datos vacíos
                    if not dataValue:
                        self.logger.warning(
                            f"⚠️ Dato vacío omitido | { dataName}"
                        )
                        continue
                    
                    await self.insertDataService.insertCaseReport(conn,radicado,dataName,dataValue)
        except Exception as e:
            self.logger.exception(f"🔴 Error al procesar datos proceso rama{e}")
            raise

    async def processActorsRama(self, conn, radicado, actorsRama ):
        try:
        
            for actor in actorsRama:
                
                if not actor: 
                    self.logger.warning(
                        f"⚠️ Dato vacío omitido para actor"
                    )
                    continue
                
                subjectType = actor["tipo_sujeto"]
                actorName = actor["nombre_actor"]
                
                await self.insertDataService.insertActorsRama(conn,radicado,subjectType,actorName)

        except Exception as e:
            self.logger.exception(f"🔴 Error al procesar actores rama {e}")
            raise


    async def filterNewActions(self, conn, radicado: str, downloadableActions: list[dict]) -> list[dict]:
        """
        Filtra las actuaciones descargables que NO existen en BD.
        Retorna la lista con solo las nuevas, incluyendo su consecutivo calculado.
        """
        try:
            consecutiveMap = {}
            newActions = []

            for action in downloadableActions:
                fecha_str = action.get("fecha")
                origin = action.get("origen_datos")

                autoDate = self._parseFecha(fecha_str)

                consecutivo, autoExists = await self.insertDataService.autoExists(
                    conn, autoDate, radicado, origin, consecutiveMap
                )

                if autoExists:
                    self.logger.info(
                        f"⏭️ Ya existe en BD → RADICACION={radicado} "
                        f"FECHA={autoDate} CONSECUTIVO={consecutivo} — se omite"
                    )
                    continue

                newActions.append({
                    **action,
                    "consecutivo": consecutivo,
                    "autoDate": autoDate,
                })

            self.logger.info(
                f"🔍 Filtrado completado → {len(newActions)}/{len(downloadableActions)} "
                f"actuaciones nuevas para descargar"
            )
            return newActions

        except Exception as e:
            self.logger.exception(f"🔴 Error filtrando actuaciones existentes: {e}")
            raise


    async def processActions(self, conn, radicado, downloadableActions, outputdir, tab: Tab):
        try:
        
            await tab.execute_script("""document.querySelectorAll("div[id^='pnlSeguimiento']").forEach(e => e.style.display = 'block');""")
            for action in downloadableActions:
                panel_id   = action.get("panel_id")
                autoDate   = action.get("autoDate")       # ✅ Ya calculado
                consecutivo = action.get("consecutivo")   # ✅ Ya calculado
                actuacion  = action.get("actuacion_rama")
                origin     = action.get("origen_datos")

                self.logger.info(f"🔹 Procesando actuación → {panel_id}")
                self.logger.info(f"📅 Fecha: {autoDate} | 📄 Actuación: {actuacion}")

                base_xpath = f"//div[@id='{panel_id}']"

                # 1️⃣ Buscar enlace de descarga
                download_el = await tab.find(
                    xpath=f"{base_xpath}//a[contains(@class,'aDescarg')]",
                    timeout=5
                )

                #  2️⃣ Registrar archivos existentes ANTES del clic
                before = set(os.listdir(outputdir))

                # 3️⃣  Clic para disparar la descarga
                await download_el.click()

                #  4️⃣ Esperar que aparezca el archivo
                try:
                    filePath, mimeType = await self.downloadHelper.waitForDownload(outputdir, timeoutSeconds=30)
                except TimeoutError:
                    self.logger.error(f"⏰ Timeout descargando acción {panel_id}")
                    continue

                #5️⃣  Obtener el processor según tipo de archivo
                try:
                    processor = await self.processorFactory.getProcessor(mimeType, "")
                except ValueError as e:
                    self.logger.warning(f"⚠️ Tipo no soportado para {panel_id}: {e}")
                    continue

                # 6️⃣ Procesar (convertir si es DOCX, pasar directo si es PDF)
                try:
                    result = await processor.processFile(filePath)
                    pdfPath = result['pdfPath']
                    self.logger.info(f"✅ Procesado → {pdfPath}")
                except Exception as e:
                    self.logger.exception(f"🔴 Error procesando archivo {filePath}: {e}")
                    continue

                # 7️⃣   insertar en BD 
                newFilePath = await self.insertDataService.insertAuto(autoDate,radicado,origin,conn, outputdir, pdfPath, consecutivo)

        except Exception as e:
            self.logger.exception(f"🔴 Error al procesar el procesar las actuaciones {e}")
            raise 

    # ✅ Método privado para parsear la fecha en múltiples formatos
    def _parseFecha(self, fecha_str: str) -> date:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(fecha_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Formato de fecha no reconocido: '{fecha_str}'")