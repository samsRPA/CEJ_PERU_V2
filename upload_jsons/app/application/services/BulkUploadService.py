

from pathlib import Path
import shutil
from app.domain.interfaces.IBulkUploadService import IBulkUploadService
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.CargaMasivaCJRepository import CargaMasivaCJRepository
import os
import json
from datetime import datetime
import math  
import logging
from datetime import datetime

import time
class BulkUploadService(IBulkUploadService):
    logger = logging.getLogger(__name__)

    def __init__( self, db: IDataBase, repository:CargaMasivaCJRepository):
        self.db= db
        self.repository = repository


    def _unificar_ndjson(self):
        """
        Convierte todos los archivos .ndjson dentro de /app/output/jsons
        a un .json con el mismo nombre, en formato de arreglo.
        """
        base_dir = Path("/app/output")
        base_path = os.path.join(base_dir, "jsons")

        if not os.path.exists(base_path):
            print(f"❌ Carpeta no encontrada: {base_path}")
            return

        # Buscar todos los archivos .ndjson en la carpeta
        archivos_ndjson = [
            f for f in os.listdir(base_path) if f.endswith(".ndjson")
        ]

        if not archivos_ndjson:
            print("⚠️ No se encontraron archivos .ndjson.")
            return

        for archivo in archivos_ndjson:
            ruta_ndjson = os.path.join(base_path, archivo)

            # Crear nombre de salida .json
            nombre_base = archivo.replace(".ndjson", "")
            ruta_json = os.path.join(base_path, f"{nombre_base}.json")

            registros = []

            # Leer NDJSON línea por línea
            with open(ruta_ndjson, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea:
                        continue
                    try:
                        registros.append(json.loads(linea))
                    except json.JSONDecodeError:
                        print(f"⚠️ Línea inválida en {archivo}: {linea}")

            # Guardar JSON normal
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(registros, f, ensure_ascii=False, indent=4)

            print(f"✅ Convertido: {ruta_json} ({len(registros)} registros)")


            

    def carga_masiva(self):
        """
        Busca la carpeta con la fecha actual dentro de output/jsons,
        lee los archivos JSON y ejecuta el procedimiento de cargue masivo.
        Además, limpia los datos de CJ_ACTORES y elimina la propiedad 'ubicacion'
        de todos los registros de CEJ_PERU antes de insertar.
        """
        conn = None
        try:
            self._unificar_ndjson()

            time.sleep(60)   # duerme 5 segundos
      
            base_dir = Path("/app/output")
            base_path = os.path.join(base_dir, "jsons")

            if not os.path.exists(base_path):
                raise FileNotFoundError(f"No existe carpeta para la fecha: {base_path}")

            resultados = {}

            archivos = {
                "CEJ_PERU": "actuaciones.json",
                "CEJ_ACTORES": "sujetos.json"
            }

            conn = self.db.acquire_connection()

            for tipo, filename in archivos.items():
                file_path = os.path.join(base_path, filename)

                if not os.path.exists(file_path):
                    resultados[tipo] = f"Archivo no encontrado: {file_path}"
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    json_content = json.load(f)
                       # 🔥 SOLO CEJ_PERU TIENE FECHAS PROBLEMÁTICAS
                if tipo == "CEJ_PERU":
                    total_original = len(json_content)
                    json_content = self._filtrar_registros_fechas_invalidas(json_content)
                    self.logger.info(
                        f"🧹 CEJ_PERU depurado: {total_original} → {len(json_content)}"
                    )

                # Convertir a string para insertarlo
                  # Convertir a string para Oracle
                json_str = json.dumps(json_content, ensure_ascii=False)

                # Insert masivo
                insertado = self.repository.insert_masivo(conn, tipo, json_str)

                if insertado:
                    self.logger.info(f"✅ Insert masivo exitoso para {tipo}")
                else:
                    self.logger.error(f"❌ Falló inserción para {tipo}")

            return resultados

        except Exception as e:
            self.logger.error(f"❌ Error inesperado en carga_masiva: {e}")

        finally:
        
            ruta = Path("/app/output/descargas")

            # if ruta.exists() and ruta.is_dir():
            #     shutil.rmtree(ruta)

            try:
                json_dir = Path("/app/output/jsons")

                if json_dir.exists():
                    for item in json_dir.iterdir():
                        if item.is_file():
                            item.unlink()  # eliminar archivo
                        elif item.is_dir():
                            shutil.rmtree(item)  # eliminar carpeta y su contenido

                    self.logger.info("🧹 Carpeta jsons limpiada correctamente.")

            except Exception as cleanup_error:
                self.logger.error(f"⚠ Error al limpiar la carpeta jsons: {cleanup_error}")

            if conn:
                self.db.release_connection(conn)




    def _filtrar_registros_fechas_invalidas(self, registros):
        """
        Elimina SOLO los registros que tengan fechas inválidas.
        Campos validados:
        - fecha -> DD-MM-YYYY
        - fecha_registro_tyba -> DD-MM-YYYY HH:MM:SS
        """
        registros_validos = []

        for r in registros:
            try:
                if r.get("fecha"):
                    datetime.strptime(r["fecha"], "%d-%m-%Y")

                if r.get("fecha_registro_tyba"):
                    datetime.strptime(
                        r["fecha_registro_tyba"],
                        "%d-%m-%Y %H:%M:%S"
                    )

                registros_validos.append(r)

            except ValueError as e:
                self.logger.warning(
                    f"🗑 Registro eliminado por fecha inválida | "
                    f"radicado={r.get('radicado')} | error={e}"
                )

        return registros_validos
