

from app.domain.interfaces.IFileProcessor import IFileProcessor
from app.domain.interfaces.IFileProcessor import IFileProcessor

class PdfProcessor(IFileProcessor):
    
    async def downloadFile(self, linkUrl: str, fileName: str, outputDir) -> str:
        raise NotImplementedError("PDF se descarga vía browser, no por URL")

    async def processFile(self, filePath: str, linkUrl: str = None) -> dict:
        return {"pdfPath": filePath}

    def getFileType(self) -> int:
        return 1