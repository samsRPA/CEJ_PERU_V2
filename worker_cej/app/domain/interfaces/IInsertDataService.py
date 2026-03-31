from abc import ABC, abstractmethod

class IInsertDataService(ABC):
    
    @abstractmethod
    async def  insertCaseReport(self,conn, radicado, dataName, dataValue):
        pass

    @abstractmethod
    async def  insertActorsRama(self,conn, radicado, subjectType, actorName):
        pass


    @abstractmethod
    async def insertAuto(self, autoDate, radicado,  origin, conn,  outputDir, originalFilePath,consecutivo):
        pass
    
    @abstractmethod
    async def autoExists(self, conn, autoDate, radicado, origin, consecutiveMap) -> bool:
        pass

