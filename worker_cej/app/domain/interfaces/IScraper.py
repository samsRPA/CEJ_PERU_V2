from abc import ABC, abstractmethod

from pydoll.browser.tab import Tab

class IScraper(ABC):
    
    @abstractmethod
    async def scraping( self,radicado:str,conn, outputDir, tab:Tab ):
        ...
  