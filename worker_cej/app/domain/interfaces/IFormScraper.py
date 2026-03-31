from abc import ABC, abstractmethod
from app.application.dto.BotReq import BotReq
from pydoll.browser.tab import Tab
class IFormScraper(ABC):

    @abstractmethod
    async def getHtml(self,tab:Tab):
        pass

    @abstractmethod
    async def fillOutForm(self, tab:Tab, data: BotReq):
        pass