from abc import ABC, abstractmethod
from pathlib import Path

class IProcessDataService(ABC):


    @abstractmethod
    async def processCaseReport(self, conn, radicado, caseReport):
        pass

    @abstractmethod
    async def processActorsRama(self, conn, radicado, actorsRama ):
        pass


    @abstractmethod
    async def filterNewActions(self, conn, radicado: str, downloadableActions: list[dict]) -> list[dict]:
        pass

    @abstractmethod
    async def processActions(self, conn, radicado, downloadableActions, outputdir ):
        pass


    

    