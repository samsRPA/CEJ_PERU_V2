from typing import Callable
from app.domain.interfaces.IProcessorFactory import IProcessorFactory
from app.domain.interfaces.IFileProcessor import IFileProcessor

class ProcessorFactory(IProcessorFactory):
    def __init__(self, processorMap: dict[str, Callable[[], IFileProcessor]]):
        self.processorMap = processorMap

    async def getProcessor(self, contentType: str, url: str) -> IFileProcessor:
        contentTypeKey = contentType.split(";")[0].strip().lower()

        allowedTypes = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "application/octet-stream"
        }

        if contentTypeKey not in allowedTypes:
            raise ValueError(f"Tipo no soportado: {contentType}")

        return self.processorMap[contentTypeKey]()