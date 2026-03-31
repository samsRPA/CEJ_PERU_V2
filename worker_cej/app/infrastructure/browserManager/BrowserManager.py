import shutil
import logging
import asyncio
import tempfile
from pathlib import Path
from user_agent import generate_user_agent

from pydoll.constants import Key
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.interactions.mouse import MouseTimingConfig
from app.domain.interfaces.IBrowserManager import IBrowserManager


class BrowserManager(IBrowserManager):
    def __init__(self,proxy):
        self._tab = None
        self._browser = None
        self._started = False
        self._profileDir = None
        self.Key = Key
        self._lock = asyncio.Lock()
        self.proxy = proxy
        self.logger = logging.getLogger(__name__)
        

    @property
    def isStarted(self) -> bool:
        return self._started and self._browser is not None

    async def restart(self):
        async with self._lock:
            self.logger.warning("♻️ Reiniciando navegador completo...")

            if self._browser:
                try:
                    await self._browser.__aexit__(None, None, None)
                except Exception:
                    pass

            self._browser = None
            self._tab = None
            self._started = False

            if self._profileDir and self._profileDir.exists():
                try:
                    shutil.rmtree(self._profileDir, ignore_errors=True)
                    self.logger.info("🧹 Perfil temporal eliminado.")
                except Exception as e:
                    self.logger.warning(f"No se pudo eliminar perfil: {e}")

            self._profileDir = None

            # ✅ Llamar a _start() interno, sin lock
            await self._start()

    async def start(self):
        async with self._lock:
            if self._started:
                self.logger.info("🟡 BrowserManager ya estaba iniciado.")
                return
            await self._start()

    async def _start(self):
        """Lógica pura de inicio, sin lock. Llamar solo desde dentro del lock."""
        profileDir = None
        try:
            ua = generate_user_agent()
            profileDir = Path(tempfile.mkdtemp(prefix="pydoll_"))

            self.logger.info("🌐 Iniciando navegador Pydoll...")

            options = ChromiumOptions()
            options.binary_location = "/usr/bin/chromium"
            options.add_argument(f"--proxy-server={self.proxy}")
            options.add_argument(f"--user-data-dir={profileDir}")
            options.add_argument(f"--user-agent={ua}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--lang=es-CO")

            options.open_pdf_externally = True
            options.prompt_for_download = False
            options.allow_automatic_downloads = True
            options.block_popups = False
            options.block_notifications = True

            browser = Chrome(options=options)
            self._tab = await browser.start()

            await self._tab.execute_script(
                """
                    Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
                    Object.defineProperty(navigator,'platform',{get:()=>'Win32'});
                    Object.defineProperty(navigator,'vendor',{get:()=>'Google Inc.'});
                    window.chrome = {runtime:{}};
                """
            )

            self._tab.mouse.timing = MouseTimingConfig(
                fitts_a=0.11,
                fitts_b=0.22,
                curvature_min=0.18,
                curvature_max=0.42,
                tremor_amplitude=1.6,
                overshoot_probability=0.92,
                min_duration=0.18,
                max_duration=4.0,
                frame_interval=0.014,
            )

            self._profileDir = profileDir
            self._browser = browser
            self._started = True

            self.logger.info("🔵 BrowserManager iniciado exitosamente.")

        except Exception as e:
            self.logger.exception(f"🔴 Error crítico iniciando el navegador: {e}")

            if profileDir and profileDir.exists():
                shutil.rmtree(profileDir, ignore_errors=True)

            if self._browser:
                try:
                    await self._browser.__aexit__(None, None, None)
                except Exception:
                    pass

            self._browser = None
            self._tab = None
            self._started = False
            raise

    async def setDownloadDirectory(self, path: str):
        if not self._tab:
            raise RuntimeError("Tab no disponible")
        
        command = {
            "method": "Browser.setDownloadBehavior",
            "params": {
                "behavior": "allow",
                "downloadPath": path,
                "eventsEnabled": True,
            }
        }
        
        await self._tab._execute_command(command)
        self.logger.info(f"📥 Directorio de descarga configurado: {path}")
    async def getBrowser(self):
        if not self.isStarted or not self._tab:
            raise RuntimeError("BrowserManager no iniciado o tab no disponible")
        try:
            return self._tab
        except Exception as e:
            self.logger.error(f"🔴 Error creando nueva tab: {e}")
            raise


    async def close(self):
        async with self._lock:
            if not self._browser:
                self.logger.info("🟡 Browser ya estaba cerrado.")
                return

            try:
                await self._browser.__aexit__(None, None, None)
                self.logger.info("🔌 Navegador cerrado correctamente.")

            except Exception as e:
                self.logger.exception(f"🔴 Error cerrando el navegador: {e}")
                raise
            
            finally:
                self._browser = None
                self._started = False
                
                if self._profileDir and self._profileDir.exists():
                    try:
                        shutil.rmtree(self._profileDir, ignore_errors=True)
                        self.logger.info("🧹 Perfil temporal eliminado.")
                    except Exception as e:
                        self.logger.warning(f"No se pudo eliminar el perfil temporal: {e}")

                self._profileDir = None
