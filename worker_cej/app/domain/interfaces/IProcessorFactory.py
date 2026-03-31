from abc import ABC, abstractmethod

from app.domain.interfaces.IFileProcessor import IFileProcessor

class IProcessorFactory(ABC):
    @abstractmethod
    async def getProcessor(self, contentType: str, url:str) -> IFileProcessor:
        pass
