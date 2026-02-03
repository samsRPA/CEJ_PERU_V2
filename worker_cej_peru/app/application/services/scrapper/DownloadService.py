import os
import json
import logging
from datetime import datetime
import shutil
import time
from app.domain.interfaces.IDownloadService import IDownloadService
from app.domain.interfaces.IS3Manager import IS3Manager
from app.infrastucture.database.repositories.DocumentsRepository import DocumentsRepository
from pydoll.browser.tab import Tab
import os
import time
import mimetypes
import asyncio
import subprocess
from app.domain.interfaces.IFileManagerService import IFileManagerService

class DownloadService(IDownloadService):
    def __init__(self,S3_manager:IS3Manager,repository: DocumentsRepository,  file_manager:IFileManagerService):
        self.logger = logging.getLogger(__name__)
        self.S3_manager = S3_manager
        self.file_manager = file_manager
        
        self.repository=repository


    async def upload_data(self, tab ,radicado, court_office_code, conn, case_download_dir, data_process_rama, actors_rama):
        try:
            #insertar proceso rama
            await self._insert_data_process_actors_rama( radicado, data_process_rama, conn, actors_rama)
            
            # 🔓 Mostrar todos los paneles
            await tab.execute_script("""
                document.querySelectorAll("div[id^='pnlSeguimiento']")
                .forEach(e => e.style.display = 'block');
            """)

            # 📋 Obtener IDs de paneles
            raw = await tab.execute_script("""
            const ids = Array.from(
            document.querySelectorAll("div[id^='pnlSeguimiento']")
            ).map(e => e.id);
            return ids;
            """, return_by_value=True)

            panel_ids = raw["result"]["result"]["value"]


            resoluciones = []
            consecutive_map = {}


            

            for idx, panel_id in enumerate(panel_ids, start=1):
                self.logger.info(f"🔹 Procesando panel {idx} → {panel_id}")

                base_xpath = f"//div[@id='{panel_id}']"
                data = {}

                # -----------------------------
                # MENSAJES DE ADVERTENCIA
                # -----------------------------
                downloadable = True
                fecha_res = None

                try:
                    msg_el = await tab.find(
                        xpath=f"{base_xpath}//div[contains(@class,'sinResol')]",
                        timeout=1
                    )
                    msg = (await msg_el.text).strip()

                    self.logger.info(f"⚠️ Mensaje panel {idx}: {msg}")

                   
                    if   msg:
                        fecha_res = await self._safe_text(
                        tab,
                        base_xpath,
                        "//div[contains(@class,'fleft')][1]"
                        )
                        downloadable = False

            
                except:
                    # 🔹 Sin advertencia
                    fecha_res = await self._safe_text(
                        tab, base_xpath,
                        "//div[div[contains(.,'Fecha de Resolución:')]]/div[contains(@class,'fleft')]"
                    )

                    if not fecha_res:
                        fecha_res = await self._safe_text(
                            tab, base_xpath,
                            "//div[div[contains(.,'Fecha de Ingreso:')]]/div[contains(@class,'fleft')]"
                        )
                        downloadable = False

                # -----------------------------
                # PARSEO DE FECHA
                # -----------------------------
                fecha_formateada = None
                fecha_registro_tyba = "00-00-0000 00:00:00"
                fecha_obj=None
                if fecha_res:
                    try:
                        if len(fecha_res) == 10:
                            fecha_obj = datetime.strptime(fecha_res, "%d/%m/%Y")
                            fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
                            fecha_registro_tyba = fecha_obj.strftime("%d-%m-%Y 00:00:00")
                        else:
                            fecha_obj = datetime.strptime(fecha_res, "%d/%m/%Y %H:%M")
                            fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
                            fecha_registro_tyba = fecha_obj.strftime("%d-%m-%Y %H:%M:%S")
                    except:
                        self.logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_res}")

                # -----------------------------
                # DATOS
                # -----------------------------
                data["radicado"] = radicado
                data["cod_despacho_rama"] = court_office_code
                data["fecha"] = fecha_formateada
                data["actuacion_rama"] = await self._safe_text(
                    tab, base_xpath,
                    "//div[contains(.,'Acto:')]/following-sibling::div[contains(@class,'fleft')]"
                )
                data["anotacion_rama"] = await self._safe_text(
                    tab, base_xpath,
                    "//div[div[contains(.,'Sumilla:')]]/div[contains(@class,'fleft')]"
                )
                data["origen_datos"] = "CEJ_PERU"
                data["fecha_registro_tyba"] = fecha_registro_tyba
                #data["downloadable"] = downloadable


                exists_action = await self.repository.exists_action( conn, data)
                
                if not exists_action:
                    

                    resoluciones.append(data)
               
                
                if downloadable:
                    dataToCheck = {
                        "FECHA_NOTIFICACION": fecha_obj,
                        "RADICACION": radicado,
                        }
                    
                    key = f"{radicado}-{fecha_formateada}"
                    if key in consecutive_map:
                        consecutivo = consecutive_map[key]
                        consecutive_map[key] = consecutivo + 1
                    else:
                        max_consecutivo = await self.repository.get_max_consecutive(conn, dataToCheck)
                        consecutivo = max_consecutivo + 1
                        consecutive_map[key] = consecutivo + 1

                    ruta_S3 = f"{fecha_formateada}_{radicado}_{consecutivo}"
                    
                    dataToCheck["CONSECUTIVO"] = consecutivo

                        
                    exists = await self.repository.exists_document(conn, dataToCheck)

                    if exists:
                        continue

                    #case_download_dir.mkdir(parents=True, exist_ok=True)
                    time.sleep(1)

                    is_insert_s3 = await self._download_records( tab,  fecha_formateada, radicado, data, consecutivo, case_download_dir,consecutive_map,base_xpath, idx)

                    if not is_insert_s3:
                        self._rollback_consecutive( consecutive_map, key)
                        continue

                    insert_bd= await self.repository.insert_document(conn,fecha_formateada,radicado,consecutivo,ruta_S3,"",data["origen_datos"],"pdf",fecha_registro_tyba)

                    if not insert_bd:
                        continue
                            
                    self.logger.info(f" ✅ Insertado en control autos rama 1 con radicado {radicado}, fecha {fecha_formateada} y consecutivo {consecutivo} ")     

            try:
                jsons_dir = "/app/output/jsons"
                os.makedirs(jsons_dir, exist_ok=True)

                file_path = f"{jsons_dir}/actuaciones.ndjson"

                        # Append línea por línea (no se corrompe)
                with open(file_path, "a", encoding="utf-8") as f:
                    for r in resoluciones:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")

                self.logger.info(f"📝 {len(resoluciones)} actuaciones agregadas a {file_path}")

            except Exception as e:
                self.logger.error(f"❌ Error guardando NDJSON: {e}")

            self.logger.info(f"✅ Total actuaciones extraídas: {len(resoluciones)}")
            
            return resoluciones
        except Exception as e:
            self.logger.error(f"❌ Error  en subir la informacion: {e}")
      
   
               
    async def _insert_data_process_actors_rama(self, radicado, data_process_rama, conn, actors_rama):

        for dato_nombre, dato_valor in data_process_rama.items():

            # ⚠️ Omitir datos vacíos
            if not dato_valor:
                self.logger.warning(
                    f"⚠️ Dato vacío omitido | {dato_nombre}"
                )
                continue

            existe = await self.repository.dato_proceso_rama_existe(
                conn=conn,
                radicado=radicado,
                dato_nombre=dato_nombre,
                dato_valor=str(dato_valor),
                origen="CEJ_PERU"
            )

            if not existe:
                await self.repository.insertar_dato_proceso_rama(
                    conn=conn,
                    radicado=radicado,
                    dato_nombre=dato_nombre,
                    dato_valor=str(dato_valor),
                    usuario="CEJ_PERU",
                    origen="CEJ_PERU"
                )
        for actor in actors_rama:
            
            if not actor: 
                self.logger.warning(
                    f"⚠️ Dato vacío omitido para actor"
                )
                continue
            tipo = actor["tipo_sujeto"]
            nombre = actor["nombre_actor"]
            
            exits_actor = await self.repository.actor_rama_existe(conn,radicado,tipo,nombre)
            
            if not exits_actor:
                
                await self.repository.insertar_actor_rama(conn,radicado,tipo,nombre)

        await conn.commit()

        

    async def _safe_text(self, tab:Tab, base_xpath, rel_xpath):
        try:
            el = await tab.find(
                xpath=f"{base_xpath}{rel_xpath}",
                timeout=2
            )
            texto = await el.text
            return texto.strip()
        except:
            return None




    async def _download_records(self,tab,fecha_formateada,radicado,data,consecutivo,case_download_dir,consecutive_map,base_xpath,idx):
        key = f"{radicado}-{fecha_formateada}"
            
        try:
            
                self.logger.info(f"⬇️ Descargando archivo panel {idx}")

                # 📌 Archivos existentes ANTES de descargar
                before_files = set(os.listdir(case_download_dir))

                # 🔎 Buscar enlace de descarga
                download_el = await tab.find(
                    xpath=f"{base_xpath}//a[contains(@class,'aDescarg')]",
                    timeout=5
                )

                href =  download_el.get_attribute("href")
                if not href:
                    self.logger.error("No se pudo obtener href de descarga")
                    return False

                # 🚀 Forzar descarga
                await tab.execute_script(f'window.location.href = "{href}";')
                self.logger.info(f"📥 URL de descarga lanzada (panel {idx})")

                # ⏳ Esperar aparición de archivo nuevo
                archivo_reciente = await self._wait_for_new_file(
                    case_download_dir,
                    before_files
                )

                if not archivo_reciente:
                    #self._rollback_consecutive(self, consecutive_map, key)
                    self.logger.error("No apareció ningún archivo descargado")
                    return False
                
                if not self.validate_and_cleanup_file(archivo_reciente):
                    self.logger.warning("⚠️ Archivo eliminado: no es PDF ni Word")
                    return False

                # ⏳ Esperar estabilidad del archivo
                if not self.wait_for_file_stable(archivo_reciente):
                    #self._rollback_consecutive(self, consecutive_map, key)
                    self.logger.error(f"Archivo inestable: {archivo_reciente}")
                    return False

                # 🧾 Detectar tipo MIME
                mime_type, _ = mimetypes.guess_type(archivo_reciente)
                self.logger.info(f"📄 MIME detectado: {mime_type}")

                # 🔄 Convertir si no es PDF
                if mime_type != "application/pdf":
                    pdf_path = os.path.splitext(archivo_reciente)[0] + ".pdf"
                    convertido = await self.convert_to_pdf(archivo_reciente, pdf_path)

                    if not convertido:
                        #self._rollback_consecutive(self, consecutive_map, key)
                        self.logger.error("Falló conversión a PDF")
                        return False

                    os.remove(archivo_reciente)
                    archivo_reciente = pdf_path
                    self.logger.info("🧩 Archivo convertido a PDF")

                # 📝 Renombrar
                nuevo_nombre = f"{fecha_formateada}_{radicado}_{consecutivo}.pdf"
                nuevo_path = os.path.join(case_download_dir, nuevo_nombre)

                os.rename(archivo_reciente, nuevo_path)
                self.logger.info(f"✅ Archivo renombrado: {nuevo_nombre}")

                #☁️ Subir a S3
                subida_ok = self.S3_manager.uploadFile(nuevo_path)
                if not subida_ok:
                    self.logger.error("Falló subida a S3")
                    return False

                return True

        except Exception as e:
            self.logger.error(f"❌ Error descarga panel {idx}: {e}")

            #self._rollback_consecutive(self, consecutive_map, key)

            return False

    def validate_and_cleanup_file(self, file_path: str) -> bool:
        """
        Valida si el archivo es PDF o Word.
        Si no lo es, lo elimina.

        Retorna True si es válido, False si fue eliminado.
        """

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False

        # Detectar MIME
        mime_type, _ = mimetypes.guess_type(file_path)

        # Extensión
        ext = os.path.splitext(file_path)[1].lower()

        allowed_mimes = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        allowed_exts = {".pdf", ".doc", ".docx"}

        is_valid = (
            mime_type in allowed_mimes or
            ext in allowed_exts
        )

        if not is_valid:
            try:
                os.remove(file_path)
                return False
            except Exception as e:
                # por si falla el borrado
                return False

        return True

    def _rollback_consecutive(self, consecutive_map, key):
               # 🔙 Rollback consecutivo
            if consecutive_map and key in consecutive_map:
                consecutive_map[key] -= 1
                self.logger.info(f"↩️ Revertido consecutivo para {key}")



    async def convert_to_pdf(self, input_path: str, output_path: str) -> bool:
        try:
            subprocess.run([
                "libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                os.path.dirname(output_path), input_path
            ], check=True)
            self.logger.info(f"✅ Archivo convertido correctamente con LibreOffice: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error al convertir {input_path} con LibreOffice: {e}", exc_info=True)
            return False
        pass

    def wait_for_file_stable(self, path, timeout=15):
        start = time.time()
        last_size = -1

        while time.time() - start < timeout:
            if not os.path.exists(path):
                time.sleep(0.2)
                continue

            # ❌ Si es directorio, abortar
            if not os.path.isfile(path):
                return False

            size = os.path.getsize(path)

            if size == last_size and size > 0:
                return True

            last_size = size
            time.sleep(0.5)

        return False

    async def _wait_for_new_file(self, directory, before_files, timeout=30):
        start = time.time()

        while time.time() - start < timeout:
            current_files = set(os.listdir(directory))
            diff = current_files - before_files

            for name in diff:
                # ❌ Ignorar temporales
                if (
                    name.startswith(".") or
                    name.endswith(".crdownload") or
                    name.startswith("org.chromium") or
                    ".org.chromium" in name
                ):
                    continue

                file_path = os.path.join(directory, name)

                # ❌ Ignorar directorios
                if not os.path.isfile(file_path):
                    continue

                return file_path

            await asyncio.sleep(0.5)

        return None


    def wait_for_file_stable(self, path, timeout=15):
        start = time.time()
        last_size = -1

        while time.time() - start < timeout:
            if not os.path.exists(path):
                time.sleep(0.2)
                continue

            # ❌ Si es directorio, abortar
            if not os.path.isfile(path):
                return False

            size = os.path.getsize(path)

            if size == last_size and size > 0:
                return True

            last_size = size
            time.sleep(0.5)

        return False

