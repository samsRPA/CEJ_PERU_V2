from abc import ABC, abstractmethod

class IScraperService(ABC):
    @abstractmethod
    async def handleMessage(self, body: bytes):
        ...