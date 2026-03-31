from typing import Dict, Optional
from abc import ABC, abstractmethod

class ICEJPeruService(ABC):
    @abstractmethod
    async def publishCaseNumber(self, caseNumber:str):
        ...  
    
    @abstractmethod
    async def publishAllCaseNumbers(self):
        ...
        