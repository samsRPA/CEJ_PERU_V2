
import asyncio
import logging
import os
import time
from pydoll.browser.tab import Tab
from app.domain.interfaces.IGetRecordsService import IGetRecordsService
import re
import json
import pandas as pd
from pydoll.exceptions import WaitElementTimeout
class GetRecordsService(IGetRecordsService):

    
    def __init__(self):
        self.logger=logging.getLogger(__name__)
        

    async def get_records_by_code( self, tab: Tab, radicado: str):
            try:
                # 🔹 Click en pestaña "Por Código de Expediente"
                tab_codigo = await tab.find(xpath="//a[contains(text(), 'Por Código de Expediente')]",timeout=15)

                await tab_codigo.scroll_into_view()
                time.sleep(1)
                await tab_codigo.click()

                self.logger.info("🟢 Click en 'Por Código de Expediente'")

                # 🔹 Separar radicado
                partes = radicado.split("-")
                if len(partes) != 7:
                    self.logger.warning(f"⚠️ Formato de radicado inválido: {radicado}")
                    return

                self.logger.info(f"📦 Radicado a llenar: {radicado}")

                # 🔹 IDs de inputs
                input_ids = ["cod_expediente","cod_anio","cod_incidente","cod_distprov", "cod_organo", "cod_especialidad", "cod_instancia"]

                # 🔹 Llenar inputs
                for i, input_id in enumerate(input_ids):
                    input_element = await tab.find(id=input_id, timeout=100)

                    await input_element.scroll_into_view()
                    time.sleep(1)
                    await input_element.type_text(partes[i],humanize=True)

                self.logger.info("✅ Radicado cargado correctamente")

            except Exception as e:
                self.logger.error(f"❌ Error en búsqueda por código: {e}")


    async def get_case_and_court( self, tab:Tab ) :
        try:
            radicado_el = await tab.find(xpath="(//div[@id='divDetalles']//div[contains(@class,'divGLRE')]//div[@class='divNroJuz']//b)[1]", timeout=5 )
            case = (await radicado_el.text).strip()
            court_el = await tab.find( xpath="(//div[@id='divDetalles']//div[contains(@class,'divGLRE')]//div[@class='divNroJuz']//b)[2]", timeout= 5 )
            court_office_code = (await court_el.text).strip()
            
            if case and court_office_code:
                self.logger.info(f"📄 Radicado: {case}")
                self.logger.info(f"🏛️ Juzgado: {court_office_code}")
                
                return case,court_office_code
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda el radicado o: {e}")
            return None, None


    async def get_actors( self, tab:Tab, radicado):
            try:
                # 🔹 Esperar el div de partes procesales
                partes_el = await tab.find(
                    xpath="//div[@id='divDetalles']//div[contains(@class,'divGLRE')]//div[@class='partesp']",
                    timeout=5
                )

                texto = (await partes_el.text).strip()

                # -----------------------------
                # Regex DEMANDANTE / DEMANDADO
                # -----------------------------
                patrones = re.findall(
                    r"(DEMANDANTE|DEMANDADO):\s*([^:]+?)(?=(?:DEMANDANTE|DEMANDADO|$))",
                    texto
                )

                if not patrones:
                    self.logger.warning("⚠️ No se encontraron sujetos procesales")
                    return pd.DataFrame()

                # -----------------------------
                # DataFrame
                # -----------------------------
                df = pd.DataFrame(patrones, columns=["TIPO_SUJETO", "NOMBRE_ACTOR"])

                df["NOMBRE_ACTOR"] = (
                    df["NOMBRE_ACTOR"]
                    .str.replace(r"\.$", "", regex=True)
                    .str.split(",")
                )

                df = df.explode("NOMBRE_ACTOR").reset_index(drop=True)
                df["NOMBRE_ACTOR"] = df["NOMBRE_ACTOR"].str.strip()

                # Normalizar tipo
                df["TIPO_SUJETO"] = df["TIPO_SUJETO"].replace({
                    "DEMANDANTE": "ACTOR"
                })

                # Metadatos
                df["RADICADO_RAMA"] = radicado
                df["ORIGEN_DATOS"] = "CEJ_PERU"

                df = df[[
                    "RADICADO_RAMA",
                    "TIPO_SUJETO",
                    "NOMBRE_ACTOR",
                    "ORIGEN_DATOS"
                ]]

                # -----------------------------
                # Guardar NDJSON
                # -----------------------------
                carpeta = "/app/output/jsons"
                os.makedirs(carpeta, exist_ok=True)

                file_path = f"{carpeta}/sujetos.ndjson"

                records = df.to_dict(orient="records")

                with open(file_path, "a", encoding="utf-8") as f:
                    for r in records:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")

                self.logger.info(f"📝 {len(records)} sujetos agregados a {file_path}")

                return df

            except WaitElementTimeout:
                self.logger.warning("⚠️ No se encontró el elemento div.partesp")
                return pd.DataFrame()

            except Exception as e:
                self.logger.error(f"❌ Error extrayendo sujetos procesales: {e}")
                return pd.DataFrame()



    async def get_case_report(self,tab: Tab, radicado):
        try:
            # 🔹 Esperar que cargue el grid del reporte
            await tab.find(
                xpath="//div[@id='gridRE']",
                timeout=100
            )

            def xp(label):
                return (
                    "//div[@id='gridRE']"
                    "//div[contains(@class,'celdaGridN') and "
                    f"contains(normalize-space(.),'{label}')]"
                    "/following-sibling::div[1]"
                )

            async def get_text(label):
                el = await tab.find(xpath=xp(label), timeout=5)
                texto = await el.text          # 👈 CLAVE
                return texto.strip().replace("\xa0", "")

            despacho_rama2= await get_text("Órgano Jurisdiccional")

            data = {
                "ESPECIALISTA LEGAL": await get_text("Especialista Legal"),
                "FECHA INICIO": await get_text("Fecha de Inicio"),
                "MATERIA": await get_text("Materia"),
                "ETAPA PROCESAL": await get_text("Etapa Procesal"),
                "UBICACION": await get_text("Ubicación"),
                "ESPECIALIDAD": await get_text("Especialidad"),
                "ESTADO": await get_text("Estado"),
                "DISTRITO JUDICIAL": await get_text("Distrito Judicial"),
                
                
    
            }

            return data, despacho_rama2

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo reporte del expediente: {e}")
            return None,None

    async def get_actores_rama(self, tab: Tab, radicado: str) -> list[dict]:
        """
        Extrae actores (demandantes / demandados) desde el panel CEJ
        y retorna una lista de diccionarios Python.
        """

        try:
            

            response = await tab.execute_script(
                script="""
                (() => {
                const filas = Array.from(
                    document.querySelectorAll("#collapseTwo .panelGrupo .partes")
                );

                // Si solo existe el header, no hay actores
                if (filas.length <= 1) return [];

                const filasDatos = filas.slice(1);

                return filasDatos.map(fila => {
                    const get = cls => {
                    const el = fila.querySelector(cls);
                    return el ? el.innerText.trim() : "";
                    };

                    const tipoSujeto  = get(".cPartTip.cPartI");
                    const razonSocial = get(".cNombresD");
                    const apPat       = get(".cApPaD");
                    const apMat       = get(".cApMaD");
                    const nombres     = get(".cNombD");

                    const nombreActor = razonSocial
                    ? razonSocial
                    : [nombres, apPat, apMat].filter(Boolean).join(" ");

                    return {
                    tipo_sujeto: tipoSujeto,
                    nombre_actor: nombreActor
                    };
                });
                })();
                """,
                return_by_value=True   # 🔥 CLAVE PARA PYDOLL
            )
            actores = response["result"]["result"]["value"]
            # 🔎 Logs de validación
            self.logger.info(f"✅ Actores extraídos: {len(actores)}")

            return actores

        except Exception as e:
            self.logger.error(
                f"❌ Error extrayendo actores CEJ | Radicado={radicado}: {e}",
                exc_info=True
            )
            return []

