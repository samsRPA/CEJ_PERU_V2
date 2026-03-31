from abc import ABC, abstractmethod

class IDatabase(ABC):
    
    @property
    @abstractmethod
    def isConnected(self) -> bool:
        ...  
    
    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def acquireConnection(self):
        ...

    @abstractmethod
    async def releaseConnection(self, conn):
        ...
    
    @abstractmethod
    async def commit(self, conn):
        ...
    
    @abstractmethod
    async def closeConnection(self):
        ...
