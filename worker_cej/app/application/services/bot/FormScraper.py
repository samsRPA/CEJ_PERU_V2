import asyncio
import logging
from app.application.dto.BotReq import BotReq
from pydoll.browser.tab import Tab
from app.domain.interfaces.IFormScraper import IFormScraper

class FormScraper(IFormScraper):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def getHtml(self,tab:Tab):
        try:
        
            await tab.execute_script("""document.querySelector('#divDetalles .divGLRE0 form button, #divDetalles .divGLRE1 form button').click();""")
            self.logger.info("🖱️ Click en botón 'Ver detalle de expediente'")
                    
            await asyncio.sleep(3)
            self.logger.info("🪟 Pasando al panel de extraccion de actuaciones")

            # 🔓 Mostrar todos los paneles
            await tab.execute_script("""document.querySelectorAll("div[id^='pnlSeguimiento']").forEach(e => e.style.display = 'block');""")

            await asyncio.sleep(20)   
            #Obtener HTML renderizado
            htmlResponse = await tab.execute_script("return document.documentElement.outerHTML;")

            # Extraer el HTML puro
            pureHTML = htmlResponse["result"]["result"]["value"]
            
            return pureHTML
        
        except Exception as e:
            self.logger.error(f"⚠️ Error al traer el html de las actuaciones: {e}", exc_info=True)
            return None
        
            

    async def fillOutForm(self, tab: Tab, data: BotReq):
        radicado = data.radicado

        valores_parte = [
            data.parte,
            data.nombre_completo,
            data.demandante,
            data.parte_demandante
        ]

        try:
            if not radicado:
                self.logger.warning("No se encontró el radicado")
                return False

            isCaseNumberFilled = await self._fillCaseNumberForm(tab, radicado)
            if not isCaseNumberFilled:
                return False

            for intento, valor_parte in enumerate(valores_parte, start=1):
                if not valor_parte:
                    continue

                self.logger.info(f"🔁 Intento {intento}/4 con PARTE = '{valor_parte}'")
                try:
                    ok = await self._tryWithCaptcha(tab, valor_parte)
                except TimeoutError:
                    # Timeout fatal: ningún intento posterior funcionará
                    self.logger.error(f"⏱️ Timeout fatal en intento {intento}/4. Abortando todos los intentos.")
                    return False

                if not ok:
                    continue

                if await self._isParteError(tab):
                    self.logger.warning("⚠️ No hubo resultados, reintentando...")
                    await asyncio.sleep(1.2)
                    await tab.execute_script("""
                        const el = document.getElementById('parte');
                        if (el) el.value = '';
                    """)
                    continue

                self.logger.info("✅ Expediente encontrado correctamente")
                return True

            self.logger.warning(f"❌ No se encontraron expedientes tras 4 intentos para el radicado {radicado}")
            self.logger.warning(f"❌ Se intentó con: {valores_parte}")
            return False

        except Exception as e:
            self.logger.error(f"⚠️ Error en fillOutForm: {e}", exc_info=True)
            return False

    async def _fillCaseNumberForm(self, tab: Tab, radicado: str):
        try:
            tab_codigo = await tab.find(xpath="//a[contains(text(), 'Por Código de Expediente')]", timeout=15)
            await tab_codigo.scroll_into_view()
            await asyncio.sleep(1)
            await tab_codigo.click()

            self.logger.info("🟢 Click en 'Por Código de Expediente'")

            partes = radicado.split("-")
            if len(partes) != 7:
                self.logger.warning(f"⚠️ Formato de radicado inválido: {radicado}")
                return False

            self.logger.info(f"📦 Radicado a llenar: {radicado}")

            input_ids = [
                "cod_expediente",
                "cod_anio",
                "cod_incidente",
                "cod_distprov",
                "cod_organo",
                "cod_especialidad",
                "cod_instancia"
            ]

            for i, input_id in enumerate(input_ids):
                input_element = await tab.find(id=input_id, timeout=100)
                await input_element.scroll_into_view()
                await asyncio.sleep(1)
                await input_element.type_text(partes[i], humanize=True)

            self.logger.info("✅ Radicado cargado correctamente")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda por código: {e}")
            return False

    async def _tryWithCaptcha(self, tab: Tab, parte: str) -> bool:
        try:
            # 1️⃣ Llenar parte
            parte_inp = await tab.find(id="parte", timeout=100)
            await parte_inp.scroll_into_view()
            await asyncio.sleep(1)
            await parte_inp.type_text(parte)

            # 2️⃣ Generar captcha
            btn_repro = await tab.find(id="btnRepro", timeout=100)
            await btn_repro.scroll_into_view()
            await asyncio.sleep(1)
            await btn_repro.click()

            # 3️⃣ Leer captcha con reintentos
            captcha_val = None
            for attempt in range(10):
                await asyncio.sleep(0.5)
                resp = await tab.execute_script("""
                    const el = document.getElementById('1zirobotz0');
                    if (!el) return null;
                    return el.value || el.innerText || el.textContent || null;
                """)
                captcha_val = resp["result"]["result"]["value"]
                if captcha_val:
                    break
                self.logger.debug(f"⏳ Esperando captcha... intento {attempt + 1}/10")

            if not captcha_val:
                self.logger.warning("⚠️ No se pudo obtener el captcha tras 10 intentos")
                return False

            self.logger.info(f"🔐 Captcha obtenido: {captcha_val}")

            # 4️⃣ Escribir captcha
            input_code_captcha = await tab.find(id="codigoCaptcha", timeout=100)
            await input_code_captcha.scroll_into_view()
            await asyncio.sleep(1)
            await input_code_captcha.type_text(captcha_val)
            await asyncio.sleep(1)

            # 5️⃣ Consultar
            btn_cons = await tab.find(id="consultarExpedientes", timeout=100)
            await btn_cons.scroll_into_view()
            await asyncio.sleep(1)
            await btn_cons.click()

            self.logger.info("🔎 Consulta enviada")
            await asyncio.sleep(1.5)

            return True

        except Exception as e:
            msg = str(e)
            if "Timed out" in msg or "timed out" in msg.lower():
                self.logger.error(f"⏱️ Timeout detectado con parte '{parte}': {e}")
                raise TimeoutError(msg)  # Propaga para cortar el loop en fillOutForm
            self.logger.warning(f"⚠️ Falló intento con parte '{parte}': {e}")
            return False

    async def _isParteError(self, tab: Tab) -> bool:
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
            pass

        return False