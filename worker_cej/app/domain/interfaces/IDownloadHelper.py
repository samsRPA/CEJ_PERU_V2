from pathlib import Path
from abc import ABC, abstractmethod

class IDownloadHelper(ABC):
    
    @abstractmethod
    async def waitForDownload(self, downloadDir: str, timeoutSeconds: int = 120) -> tuple[str, str]:
        pass