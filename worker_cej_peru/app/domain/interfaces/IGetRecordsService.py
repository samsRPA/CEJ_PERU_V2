from abc import ABC, abstractmethod
from pydoll.browser.tab import Tab
class IGetRecordsService(ABC):
    
    @abstractmethod
    async def get_records_by_code( self, tab: Tab, radicado: str):
        pass

    @abstractmethod
    async def get_case_and_court( self, tab:Tab ) :
        pass

    @abstractmethod
    async def get_actors( self, tab:Tab, radicado):
        pass

    @abstractmethod
    async def get_case_report(self,tab: Tab, radicado):
        pass

    @abstractmethod
    async def get_actores_rama(self, tab: Tab, radicado: str) -> list[dict]:
        pass
    
    # @abstractmethod   
    # def get_records_by_Filters(self,driver, wait,distrito_judicial,instancia, especialidad,annio,num_expediente):
    #    pass

