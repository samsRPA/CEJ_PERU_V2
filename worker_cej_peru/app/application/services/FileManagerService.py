import os
import shutil
import logging
from pathlib import Path
from contextlib import contextmanager


from app.domain.interfaces.IFileManagerService import IFileManagerService

class FileManagerService(IFileManagerService):
    
    def __init__(self,   tempFolder:str):
        self.tempFolder = Path(tempFolder)
        self.logger = logging.getLogger(__name__)

    def _createFolder(self, proceeding:str)-> Path:
        try:
            outputPath = self.tempFolder / proceeding
            outputPath.mkdir(parents=True, exist_ok=True)
            return outputPath
        except Exception as e:
            raise RuntimeError(e)
    
    def _deleteFolder(self, proceeding:str)-> None:
        folderToDelete = self.tempFolder / proceeding
        if folderToDelete.exists() and folderToDelete.is_dir():
            try:
                shutil.rmtree(folderToDelete)
            except Exception as e:
                self.logger.error(f"🔴 Error al eliminar la carpeta {folderToDelete}: {e}")

    @contextmanager
    def useTempFolder(self, proceeding: str):
        path = self._createFolder(proceeding)
        try:
            yield path
        finally:
            self._deleteFolder(proceeding)