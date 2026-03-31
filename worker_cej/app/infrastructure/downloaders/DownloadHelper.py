# app/infrastructure/browserManager/DownloadWaiter.py
import asyncio
import os
import logging
from pathlib import Path

from app.domain.interfaces.IDownloadHelper import IDownloadHelper

class DownloadHelper(IDownloadHelper):
    
    def __init__(self):
        pass
    logger = logging.getLogger(__name__)

    EXTENSION_TO_MIME = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc":  "application/msword",
    }



    async def waitForDownload(self, downloadDir: str, timeoutSeconds: int = 120) -> tuple[str, str]:
        """
        Espera a que aparezca un archivo nuevo en downloadDir (que no sea .crdownload).
        Retorna (filePath, mimeType).
        """
        before = set(os.listdir(downloadDir))
        deadline = asyncio.get_event_loop().time() + timeoutSeconds

        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(0.5)
            after = set(os.listdir(downloadDir))
            newFiles = after - before

            # Ignorar archivos temporales de Chrome
            completed = [
                f for f in newFiles
                if not f.endswith(".crdownload") and not f.endswith(".tmp")
            ]

            if completed:
                fileName = completed[0]
                filePath = os.path.join(downloadDir, fileName)
                ext = Path(fileName).suffix.lower()
                mimeType = self.EXTENSION_TO_MIME.get(ext, "application/octet-stream")
                self.logger.info(f"✅ Archivo descargado: {fileName} → {mimeType}")
                return filePath, mimeType

        raise TimeoutError(f"⏰ Timeout esperando descarga en {downloadDir}")