
import asyncio
import logging
from pathlib import Path
import shutil

from app.domain.interfaces.ICEJScrapperService import ICEJScrapperService



from app.domain.interfaces.IFormScrapper import IFormScrapper
from app.domain.interfaces.IDataBase import IDataBase
from app.domain.interfaces.IDownloadService import IDownloadService
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
import os

from pathlib import Path
from pydoll.browser import Chrome

from app.domain.interfaces.IGetRecordsService import IGetRecordsService



class CEJScrapperService(ICEJScrapperService):

    def __init__(self, url, form_scrapper:IFormScrapper, db: IDataBase, download_service:IDownloadService, getRecords: IGetRecordsService ):

        self.url=url
        self.form_scrapper = form_scrapper
        self.db=db
        self.download_service=download_service
        self.getRecords = getRecords  
        self.logger= logging.getLogger(__name__)



    async def scrapper(self,case_information):
        radicado= case_information.radicado
    
        worker_id = os.environ.get("HOSTNAME", "worker_default")

        case_download_dir = (
            Path("/app/output/descargas")
            / f"temp_{worker_id}_{radicado}"
        )
        options = ChromiumOptions()
        options.binary_location = "/usr/bin/chromium"


        # UI visible
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")


        # Descargas
        options.set_default_download_directory(str(case_download_dir))
        options.open_pdf_externally = True
        options.prompt_for_download = False
        options.allow_automatic_downloads = True
        options.block_popups = False
        options.block_notifications = True
            
        browser = None
        conn=None
        
        try:
            # 🔹 Iniciar navegador
            async with Chrome(options=options) as browser:
                self.logger.info(f"🏁 Inciando scrapper para el radicado {radicado}")
                tab = await browser.start()

                # 🔹 Abrir CEJ
                await tab.go_to(self.url,timeout=60)
            
                is_completed_form = await self.form_scrapper.fill_out_form(tab, case_information)

                if not is_completed_form:
                    self.logger.warning("⚠️ No se logro llenar el formulario completo.")
                    return
                court_office_code=None
              
                radicado_Web, court_office_code1 = await self.getRecords.get_case_and_court(tab)

                await self.getRecords.get_actors(tab,radicado)
               
                await tab.execute_script("""document.querySelector('#divDetalles .divGLRE0 form button, #divDetalles .divGLRE1 form button').click();""")
                self.logger.info("🖱️ Click en botón 'Ver detalle de expediente'")
                
                await asyncio.sleep(2)
                self.logger.info("🪟 Pasando al panel de extraccion de actuaciones")
                
                data_process_rama, court_office_code2= await self.getRecords.get_case_report(tab, radicado)
                actors_rama= await self.getRecords.get_actores_rama(tab,radicado)

                conn = await self.db.acquire_connection()
                
                if court_office_code1:
                    court_office_code= court_office_code1
                else:
                    court_office_code= court_office_code2
                    
                await self.download_service.upload_data(tab ,radicado, court_office_code, conn, case_download_dir, data_process_rama, actors_rama)

                await self.db.commit(conn)
                if browser:
                    self.logger.info("🛑 Cerrando navegador")
                    await browser.close()
                    
                self.logger.info(f" 🚩 Terminando scrapper para el radicado {radicado}")
                    
        except Exception as e:
            self.logger.exception("❌ Error durante la ejecución")

        finally:
            if case_download_dir :
                try:
                    await asyncio.sleep(15)
                    shutil.rmtree(case_download_dir)
                    self.logger.info(f"🧹 Carpeta temporal eliminada: {case_download_dir}")
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo borrar {case_download_dir}: {e}")
                    
           

            if conn:
                try:
                    await self.db.release_connection(conn)
                except Exception as e:
                    self.logger.warning(f"Error liberando conexión DB: {e}")
          



      


