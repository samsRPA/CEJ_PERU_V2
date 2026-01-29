import asyncio
import json
import logging
import os
import time

from app.domain.interfaces.IGetRecordsService import IGetRecordsService
from app.domain.interfaces.IFormScrapper import IFormScrapper
from pydoll.browser.tab import Tab

class FormScrapper(IFormScrapper):
    def __init__(self, getRecords: IGetRecordsService):
        self.getRecords = getRecords    
        self.logger = logging.getLogger(__name__)


    async def fill_out_form(self, tab:Tab, case_information):
        # distrito_judicial = case_information.distrito_judicial
        # instancia = case_information.instancia
        # especialidad = case_information.especialidad
        # annio = case_information.annio
        # num_expediente = case_information.num_expediente
        radicado = case_information.radicado

        valores_parte = [
            case_information.parte,
            case_information.nombre_completo,
            case_information.demandante,
            case_information.parte_demandante
        ]
        
        try:
            if not radicado:
                self.logger.warning("  No se  encontró el radicado")
                return
                
            self.logger.info("✅ Se encontró el radicado. Filtro por radicado.")
            await self.getRecords.get_records_by_code(tab, radicado)
    

            for intento, valor_parte in enumerate(valores_parte, start=1):
                if not valor_parte:
                    continue
                
                self.logger.info(f"🔁 Intento {intento}/4 con PARTE = '{valor_parte}'")
                ok = await self._try_parte_with_captcha(tab, valor_parte)
                if not ok:
                    continue

                if await self.is_parte_error(tab):
                    self.logger.warning("⚠️ No hubo resultados, reintentando...")
                    time.sleep(1.2)
                    await tab.execute_script("""
                    document.getElementById("parte").value = "";

                    """)
        
                    continue
                
                # ✅ ÉXITO
                self.logger.info("✅ Expediente encontrado correctamente")
                return True

                # ❌ SI LLEGAMOS AQUÍ → FALLARON LOS 4 INTENTOS
            self.logger.warning(f"❌ No se encontraron expedientes tras 4 intentos para el radicado {radicado}")
            self.logger.warning(f"❌Se intento con  {valores_parte}")
            
            return False
        except Exception as e:
            self.logger.error(f"⚠️ Error en fill_out_form: {e}", exc_info=True)
            return False


    async def _try_parte_with_captcha( self, tab: Tab, parte: str) -> bool:
        try:
            # 1️⃣ llenar parte
            parte_inp = await tab.find(id="parte", timeout=100)
            await parte_inp.scroll_into_view()
            await asyncio.sleep(1)
            await parte_inp.type_text(parte)
            
            # 2️⃣ generar captcha
            btn_repro = await tab.find(id="btnRepro", timeout=100)
            await btn_repro.scroll_into_view()
            await asyncio.sleep(1)
            await btn_repro.click()
            await asyncio.sleep(1.1)

            # 3️⃣ leer captcha oculto
            resp = await tab.execute_script("""
            const el = document.getElementById('1zirobotz0');
            return el ? el.value || el.innerText || el.textContent : null;
            """)
            captcha_val = resp["result"]["result"]["value"]
            self.logger.info(f"🔐 Captcha obtenido: {captcha_val}")
            
            # 4️⃣ escribir captcha
            input_code_captcha= await tab.find(id="codigoCaptcha", timeout=100)
            await input_code_captcha.scroll_into_view()
            await asyncio.sleep(1)
            await input_code_captcha.type_text( captcha_val )
            await asyncio.sleep(1)

            # 5️⃣ consultar
            btn_cons = await tab.find(id="consultarExpedientes", timeout=100)
            await btn_cons.scroll_into_view()
            await asyncio.sleep(1)
            await btn_cons.click()

            self.logger.info("🔎 Consulta enviada")
            await asyncio.sleep(1.5)

            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Falló intento con parte '{parte}': {e}")
            return False


    async def is_parte_error(self, tab: Tab) -> bool:
        try:
            mensaje_no = await tab.find(
                id="mensajeNoExisteExpedientes",
                timeout=3
            )
            if await mensaje_no.is_visible():
                texto = (await mensaje_no.text).strip()
                self.logger.warning(f"⚠️ Mensaje del sistema: '{texto}'")
                return True

        except Exception:
            # No existe el elemento → no hay error
            pass

        return False