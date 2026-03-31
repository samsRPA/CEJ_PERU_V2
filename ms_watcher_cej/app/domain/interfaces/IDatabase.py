from abc import ABC, abstractmethod

class IDatabase(ABC):
    
    @property
    @abstractmethod
    def isConnected(self) -> bool:
        pass  
    
    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def acquireConnection(self):
        pass

    @abstractmethod
    async def releaseConnection(self, conn):
        pass
    
    @abstractmethod
    async def commit(self, conn):
        pass
    
    @abstractmethod
    async def closeConnection(self):
        pass
