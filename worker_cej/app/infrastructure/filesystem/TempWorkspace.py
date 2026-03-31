import shutil
import logging
from pathlib import Path
from contextlib import contextmanager
from pathlib import Path

import aiofiles  # si quieres hacerlo async
import json
from typing import Union, List, Dict, Any

class TempWorkspace:
    
    def __init__(self, basePath: Path):
        self.basePath = basePath
        self.logger = logging.getLogger(__name__)
        
    def _createFolder(self, folderName: str) -> Path:
        path = self.basePath / folderName
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _deleteFolder(self, folderName: str) -> None:
        path = self.basePath / folderName
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
            except Exception as e:
                self.logger.error(f"🔴 Error al eliminar la carpeta {path}: {e}")
                


    async def appendNDJson(self, folderName: str, fileName: str, content: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Path:
        """
        Agrega uno o varios registros en formato NDJSON (Newline Delimited JSON).
        No sobreescribe el archivo, solo añade nuevas líneas.
        """

        try:
            # 🔹 Crear carpeta si no existe
            folder_path: Path = self._createFolder(folderName)

            # 🔹 Forzar extensión .ndjson
            if not fileName.endswith(".ndjson"):
                fileName = f"{fileName}.ndjson"

            file_path: Path = folder_path / fileName

            # 🔹 Normalizar a lista
            if isinstance(content, dict):
                content = [content]

            if not isinstance(content, list):
                raise ValueError("El contenido debe ser dict o list[dict]")

            # 🔹 Convertir todo a formato NDJSON en memoria (más eficiente)
            lines = []
            for item in content:
                try:
                    json_line = json.dumps(item, ensure_ascii=False)
                    lines.append(json_line)
                except TypeError as e:
                    self.logger.warning(f"⚠️ Registro no serializable omitido: {e}")

            if not lines:
                self.logger.warning("⚠️ No hay registros válidos para guardar.")
                return file_path

            # 🔹 Escritura en bloque (más rápido que escribir línea por línea)
            async with aiofiles.open(file_path, mode="a", encoding="utf-8") as f:
                await f.write("\n".join(lines) + "\n")

            self.logger.info(f"🟢 {len(lines)} registros añadidos correctamente en {file_path}")

            return file_path

        except Exception as e:
            self.logger.error(f"🔴 Error al hacer append en NDJSON {fileName}: {e}")
            raise

    

    @contextmanager
    def useTempFolder(self, folderName: str):
        path = self._createFolder(folderName)
        try:
            yield path
        finally:
            pass
           # self._deleteFolder(folderName)
