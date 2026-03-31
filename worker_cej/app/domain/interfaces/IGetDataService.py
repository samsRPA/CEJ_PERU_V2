from abc import ABC, abstractmethod


class IGetDataService(ABC):

    @abstractmethod
    def getCaseReport(self, soup, radicado):
        pass

    @abstractmethod
    def getActoresRama(self, soup, radicado: str) -> list[dict]:
         pass

    @abstractmethod
    def getActions(self, soup, radicado: str, courtOfficeCode: str) -> tuple[list[dict], list[dict]]:
        pass