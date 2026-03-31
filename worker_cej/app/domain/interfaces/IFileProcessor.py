from pathlib import Path
from abc import ABC, abstractmethod

class IFileProcessor(ABC):
    @abstractmethod
    async def downloadFile(self, linkUrl: str, fileName: str, outputDir:Path) -> str:
        pass
    
    @abstractmethod
    async def processFile(self, filePath: str, linkUrl:str) -> dict:
        pass
    
    @abstractmethod
    def getFileType()->int:
        pass