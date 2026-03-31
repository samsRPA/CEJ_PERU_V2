from abc import ABC, abstractmethod

class IBrokerProducer(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def publishMessage(self, message: dict):
        pass

    @abstractmethod
    async def close(self):
        pass
