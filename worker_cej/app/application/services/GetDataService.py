import logging
from app.domain.interfaces.IGetDataService import IGetDataService
from bs4 import BeautifulSoup
from datetime import datetime
class GetDataService(IGetDataService):
    

    
    def __init__(self):

        self.logger= logging.getLogger(__name__)


    def getCaseReport(self, soup, radicado):
        try:
         
            # 🔹 Buscar el grid del reporte
            grid = soup.find("div", id="gridRE")
            if not grid:
                self.logger.warning("⚠️ No se encontró el div#gridRE en el HTML.")
                return None, None

            def get_text(label: str) -> str:
                # Buscar la celda que contenga el label
                celda = grid.find(
                    lambda tag: (
                        tag.name == "div"
                        and "celdaGridN" in tag.get("class", [])
                        and label in tag.get_text(strip=True)
                    )
                )
                if not celda:
                    return ""
                # Obtener el siguiente div hermano
                siguiente = celda.find_next_sibling("div")
                if not siguiente:
                    return ""
                return siguiente.get_text(strip=True).replace("\xa0", "")

            despacho_rama2 = get_text("Órgano Jurisdiccional")

            data = {
                "ESPECIALISTA LEGAL": get_text("Especialista Legal"),
                "FECHA INICIO":       get_text("Fecha de Inicio"),
                "MATERIA":            get_text("Materia"),
                "ETAPA PROCESAL":     get_text("Etapa Procesal"),
                "UBICACION":          get_text("Ubicación"),
                "ESPECIALIDAD":       get_text("Especialidad"),
                "ESTADO":             get_text("Estado"),
                "DISTRITO JUDICIAL":  get_text("Distrito Judicial"),
            }

            return data, despacho_rama2

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo reporte del expediente: {e}")
            return None, None


    def getActoresRama(self, soup, radicado: str) -> list[dict]:
        """
        Extrae actores (demandantes / demandados) desde el HTML puro del panel CEJ
        y retorna una lista de diccionarios Python.
        """
        try:

        
            # Buscar todas las filas de partes dentro del panel
            filas = soup.select("#collapseTwo .panelGrupo .partes")

            # Si solo existe el header (o no hay nada), retornar vacío
            if len(filas) <= 1:
                self.logger.warning("⚠️ No se encontraron actores en el panel.")
                return []

            filas_datos = filas[1:]  # Omitir el header

            actores = []
            for fila in filas_datos:
                def get(selector: str) -> str:
                    el = fila.select_one(selector)
                    return el.get_text(strip=True) if el else ""

                tipo_sujeto  = get(".cPartTip.cPartI")
                razon_social = get(".cNombresD")
                ap_pat       = get(".cApPaD")
                ap_mat       = get(".cApMaD")
                nombres      = get(".cNombD")

                nombre_actor = (
                    razon_social
                    if razon_social
                    else " ".join(filter(None, [nombres, ap_pat, ap_mat]))
                )

                actores.append({
                    "tipo_sujeto":  tipo_sujeto,
                    "nombre_actor": nombre_actor,
                })

            self.logger.info(f"✅ Actores extraídos: {len(actores)}")
            return actores

        except Exception as e:
            self.logger.error(
                f"❌ Error extrayendo actores CEJ | Radicado={radicado}: {e}",
                exc_info=True
            )
            return []


    def getActions(self, soup, radicado: str, courtOfficeCode: str) -> tuple[list[dict], list[dict]]:
        """
        Extrae todas las actuaciones desde el HTML puro del panel CEJ.
        Retorna:
            - todas_actuaciones: lista con todas las actuaciones
            - descargables: lista solo con actuaciones que tienen archivo descargable (incluye panel_id)
        """
        try:

            panels = soup.select("div[id^='pnlSeguimiento']")

            if not panels:
                self.logger.warning("⚠️ No se encontraron paneles de seguimiento.")
                return [], []

            todas_actuaciones = []
            descargables = []

            for panel in panels:
                panel_id = panel.get("id")

                def get_field(label: str) -> str:
                    target = panel.find(
                        lambda tag: tag.name == "div"
                        and label in tag.get_text(strip=True)
                        and "roptionss" in tag.get("class", [])
                    )
                    if not target:
                        return ""
                    sibling = target.find_next_sibling("div")
                    return sibling.get_text(strip=True).replace("\xa0", "") if sibling else ""

                # ── Mensaje de advertencia (sin resolución) ──────────────────────────
                msg_el = panel.find("div", class_="sinResol")
                downloadable = True
                fecha_res = ""

                if msg_el:
                    fleft = panel.find("div", class_="fleft")
                    fecha_res = fleft.get_text(strip=True) if fleft else ""
                    downloadable = False
                else:
                    fecha_res = get_field("Fecha de Resolución:")
                    if not fecha_res:
                        fecha_res = get_field("Fecha de Ingreso:")
                        downloadable = False

                # ── Parseo de fecha ───────────────────────────────────────────────────
                fecha_formateada = None
                fecha_registro_tyba = "00-00-0000 00:00:00"
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
                    except Exception:
                        self.logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_res}")

                # ── Datos principales ─────────────────────────────────────────────────
                data = {
                    "radicado":            radicado,
                    "cod_despacho_rama":   courtOfficeCode,
                    "fecha":               fecha_formateada,
                    "actuacion_rama":      get_field("Acto:"),
                    "anotacion_rama":      get_field("Sumilla:"),
                    "origen_datos":        "CEJ_PERU",
                    "fecha_registro_tyba": fecha_registro_tyba,
                }

                # ── Validación de campos requeridos ───────────────────────────────────
                campos_invalidos = [
                    k for k, v in data.items()
                    if v is None or (isinstance(v, str) and not v.strip())
                ]
                if campos_invalidos:
                    self.logger.warning(f"⚠️ Panel {panel_id} omitido. Campos inválidos: {campos_invalidos}")
                    continue

                todas_actuaciones.append(data)

                # ── Detectar si el panel tiene botón de descarga ──────────────────────
                tiene_descarga = panel.find("div", class_="dBotonDesc") is not None
                if tiene_descarga:
                    descargables.append({
                        **data,
                        "panel_id": panel_id,
                    })

            self.logger.info(
                f"✅ Actuaciones extraídas: {len(todas_actuaciones)} total | {len(descargables)} descargables"
            )
            return todas_actuaciones, descargables

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo actuaciones CEJ | Radicado={radicado}: {e}", exc_info=True)
            return [], []