import logging
import os
import subprocess

from app.domain.interfaces.IFileProcessor import IFileProcessor

class DocxProcessor(IFileProcessor):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def convertToPdf(self, docxPath: str) -> str:
        outputDir = os.path.dirname(docxPath)
        baseName = os.path.splitext(os.path.basename(docxPath))[0]
        pdfPath = os.path.join(outputDir, f"{baseName}.pdf")

        result = subprocess.run([
            "libreoffice", "--headless",
            "--convert-to", "pdf",
            "--outdir", outputDir,
            docxPath
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Error al convertir Word a PDF:\n{result.stderr}")

        if not os.path.exists(pdfPath):
            raise FileNotFoundError(f"No se generó el PDF: {pdfPath}")

        # 🧹 Eliminar el archivo original
        try:
            os.remove(docxPath)
            self.logger.info(f"🧩 Conversión exitosa: Word → PDF 📄➡️📕 | Archivo eliminado: {docxPath}")
        except Exception as e:
            self.logger.warning(f"⚠️ PDF generado pero no se pudo eliminar el Word: {e}")

        return pdfPath

    async def downloadFile(self, linkUrl: str, fileName: str, outputDir) -> str:
        raise NotImplementedError("DOCX se descarga vía browser, no por URL")

    async def processFile(self, filePath: str, linkUrl: str = None) -> dict:
        pdfPath = await self.convertToPdf(filePath)
        return {"pdfPath": pdfPath}

    def getFileType(self) -> int:
        return 6