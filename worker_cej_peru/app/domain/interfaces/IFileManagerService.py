from abc import ABC, abstractmethod
from pathlib import Path

class IFileManagerService(ABC):
  


    @abstractmethod
    def _createFolder(self, proceeding:str)-> Path:
        pass

    @abstractmethod
    def _deleteFolder(self, proceeding:str)-> None:
        pass

    @abstractmethod
    def useTempFolder(self, proceeding: str):
        pass