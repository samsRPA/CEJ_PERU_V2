from abc import ABC, abstractmethod


class IProceedingsCEJPeruService(ABC):



    @abstractmethod
    async def publishProceedings(self):
        pass

    @abstractmethod
    async def publishProceeding(self,radicado):
        pass