import asyncio
import logging
import time

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
from pydoll.constants import By
from datetime import datetime
import os
import shutil
import tempfile
from pathlib import Path

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
import re
import json
import pandas as pd
from pydoll.exceptions import WaitElementTimeout

async def get_records_by_code( tab: Tab, radicado: str):
        try:
            # 🔹 Click en pestaña "Por Código de Expediente"
            tab_codigo = await tab.find(
                xpath="//a[contains(text(), 'Por Código de Expediente')]",
                timeout=15
            )

            await tab_codigo.scroll_into_view()
            await asyncio.sleep(0.5)
            await tab_codigo.click()

            logger.info("🟢 Click en 'Por Código de Expediente'")

            # 🔹 Separar radicado
            partes = radicado.split("-")
            if len(partes) != 7:
                logger.warning(f"⚠️ Formato de radicado inválido: {radicado}")
                return

            logger.info(f"📦 Radicado a llenar: {radicado}")

            # 🔹 IDs de inputs
            input_ids = [
                "cod_expediente",
                "cod_anio",
                "cod_incidente",
                "cod_distprov",
                "cod_organo",
                "cod_especialidad",
                "cod_instancia"
            ]

            # 🔹 Llenar inputs
            for i, input_id in enumerate(input_ids):
                input_element = await tab.find(id=input_id, timeout=10)

                await input_element.scroll_into_view()
                await asyncio.sleep(0.2)
                await input_element.type_text(partes[i])

            logger.info("✅ Radicado cargado correctamente")

        except Exception as e:
            logger.error(f"❌ Error en búsqueda por código: {e}")

def get_records_by_Filters(tab, distrito_judicial, instancia, especialidad, annio, num_expediente):
    pass

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
logger = logging.getLogger()
logging.getLogger("pydoll").setLevel(logging.CRITICAL)

async def fill_out_form(tab, case_information):
    distrito_judicial = case_information["distrito_judicial"]
    instancia = case_information["instancia"]
    especialidad = case_information["especialidad"]
    annio = case_information["annio"]
    num_expediente = case_information["num_expediente"]
    radicado = case_information["radicado"]

    valores_parte = [
        
            case_information["parte"],
            case_information["nombre_completo"],
            case_information["demandante"],
            case_information["parte_demandante"]
        ]
    try:
        if not radicado:
            logger.warning("  No se  encontró el radicado")
            return
            
        logger.info("✅ Se encontró el radicado. Filtro por radicado.")
        await get_records_by_code(tab, radicado)
   

        for intento, valor_parte in enumerate(valores_parte, start=1):
            if not valor_parte:
                continue
            
            logger.info(f"🔁 Intento {intento}/4 con PARTE = '{valor_parte}'")
            ok = await _try_parte_with_captcha(tab, valor_parte)
            if not ok:
                continue

            if await is_parte_error(tab):
                logger.warning("⚠️ No hubo resultados, reintentando...")
                time.sleep(1.2)
                await tab.execute_script("""
                document.getElementById("parte").value = "";

                """)
     
                continue
            
            # ✅ ÉXITO
            logger.info("✅ Expediente encontrado correctamente")
            return True

            # ❌ SI LLEGAMOS AQUÍ → FALLARON LOS 4 INTENTOS
        logger.warning(f"❌ No se encontraron expedientes tras 4 intentos para el radicado {radicado}")
        logger.warning(f"❌Se intento con  {valores_parte}")
        
        return False
    except Exception as e:
        logger.error(f"⚠️ Error en fill_out_form: {e}", exc_info=True)
        return False




async def _try_parte_with_captcha( tab: Tab, parte: str) -> bool:
    try:
        # 1️⃣ llenar parte
        parte_inp = await tab.find(id="parte", timeout=10)
        await parte_inp.scroll_into_view()
        await asyncio.sleep(1)


 
        
        await asyncio.sleep(0.1)
        await parte_inp.type_text(parte)

      

        # 2️⃣ generar captcha
        btn_repro = await tab.find(id="btnRepro", timeout=10)
        await btn_repro.scroll_into_view()
        await asyncio.sleep(1)
        await btn_repro.click()

        await asyncio.sleep(1.1)

        # 3️⃣ leer captcha oculto
        resp = await tab.execute_script("""
        const el = document.getElementById('1zirobotz0');
        return el ? el.value || el.innerText || el.textContent : null;
    """)

        captcha_val = resp["result"]["result"]["value"]

        logger.info(f"🔐 Captcha obtenido: {captcha_val}")

        # 4️⃣ escribir captcha

        input_code_captcha= await tab.find(id="codigoCaptcha", timeout=10)
        await input_code_captcha.scroll_into_view()
        await asyncio.sleep(1)

        await asyncio.sleep(1)
        await input_code_captcha.type_text( captcha_val )

    

        await asyncio.sleep(1)

        # 5️⃣ consultar
        btn_cons = await tab.find(id="consultarExpedientes", timeout=10)
        await btn_cons.scroll_into_view()
        await asyncio.sleep(1)
        await btn_cons.click()

        logger.info("🔎 Consulta enviada")
        await asyncio.sleep(1.5)

        return True

    except Exception as e:
        logger.warning(f"⚠️ Falló intento con parte '{parte}': {e}")
        return False


async def is_parte_error( tab: Tab) -> bool:
    try:
        mensaje_no = await tab.find(
            id="mensajeNoExisteExpedientes",
            timeout=3
        )

        if await mensaje_no.is_visible():
            texto = (await mensaje_no.text).strip()
            logger.warning(f"⚠️ Mensaje del sistema: '{texto}'")
            return True

    except Exception:
        # No existe el elemento → no hay error
        pass

    return False



async def scrapper(case_information):
 # 🔹 Logging

    # 🔹 Opciones de Chrome (CON UI)
    download_dir = Path("output/descargas").absolute()
    download_dir.mkdir(parents=True, exist_ok=True)

    options = ChromiumOptions()
    options.binary_location = "/usr/bin/google-chrome-stable"

    # UI visible
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")

    # Descargas
    options.set_default_download_directory(str(download_dir))
    options.open_pdf_externally = True
    options.prompt_for_download = False
    options.allow_automatic_downloads = True
    options.block_popups = False
    options.block_notifications = True





    num_expediente = case_information["num_expediente"]
    nombre_completo=case_information["nombre_completo"]
    annio = case_information["annio"]
    radicado= case_information["radicado"]
    try:
        # 🔹 Iniciar navegador
        async with Chrome(options=options) as browser:
            tab = await browser.start()

            # 🔹 Abrir CEJ
            await tab.go_to(
                "https://cej.pj.gob.pe/cej/forms/busquedaform.html",
                timeout=60
            )
          
            is_completed_form = await fill_out_form(tab, case_information)

            if not is_completed_form:
                logger.warning("⚠️ No se logro llenar el formulario completo.")
                return


            

          

            # -----------------------------
            # # RADICADO (primer <b>)
            # # -----------------------------
            # radicado_el = await tab.find(
            #     xpath="(//div[@id='divDetalles']//div[contains(@class,'divGLRE')]//div[@class='divNroJuz']//b)[1]",
            #     timeout=5
            # )

            # radicado_web = (await radicado_el.text).strip()

            # -----------------------------
            # JUZGADO (segundo <b>)
            # -----------------------------
            juzgado_el = await tab.find(
                xpath="(//div[@id='divDetalles']//div[contains(@class,'divGLRE')]//div[@class='divNroJuz']//b)[2]",
                timeout=5
            )

            cod_despacho_rama = (await juzgado_el.text).strip()

            # logger.info(f"📄 Radicado: {radicado_web}")
            logger.info(f"🏛️ Juzgado: {cod_despacho_rama}")

            # boton = await tab.find(
            # xpath="//div[@id='divDetalles']//div[contains(@class,'divGLRE')]//form//button",
            # timeout=5
            # )
            # await boton.click()
            #await _extract_actors_pydoll( tab, radicado)

            await tab.execute_script("""
            document
            .querySelector('#divDetalles .divGLRE0 form button, #divDetalles .divGLRE1 form button')
            .click();
            """)


            
            logger.info("🖱️ Click en botón 'Ver detalle de expediente'")

            await asyncio.sleep(2)
            logger.info("Pasando al panel de extraccion de actuaciones")
            #data_process_rama= await extract_reporte_expediente(tab, radicado)

            actors = await get_actores_rama(tab, radicado)
            logger.info(actors)
            #await extract_case_records(tab ,radicado, cod_despacho_rama,None,None)
      

           
            if browser:
                logger.info("🛑 Cerrando navegador")
                await browser.close()

    except Exception as e:
           logger.exception("❌ Error durante la ejecución")



async def safe_text(tab, base_xpath, rel_xpath):
    try:
        el = await tab.find(
            xpath=f"{base_xpath}{rel_xpath}",
            timeout=2
        )
        texto = await el.text
        return texto.strip()
    except:
        return None

async def extract_case_records(tab: Tab, radicado, cod_despacho_rama, conn, download_dir):

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

    logger.info(f"{panel_ids}")

    resoluciones = []

    for idx, panel_id in enumerate(panel_ids, start=1):
        logger.info(f"🔹 Procesando panel {idx} → {panel_id}")

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

            logger.info(f"⚠️ Mensaje panel {idx}: {msg}")

            if "no se pueden visualizar" in msg:
                fecha_res = await safe_text(
                    tab, base_xpath,
                    "//div[div[contains(.,'Fecha de Ingreso:')]]/div[contains(@class,'fleft')]"
                )
                downloadable = False

            elif "no se encuentra anexado" in msg:
                fecha_res = await safe_text(
                    tab, base_xpath,
                    "//div[div[contains(.,'Fecha de Resolución:')]]/div[contains(@class,'fleft')]"
                )
                downloadable = False

        except:
            # 🔹 Sin advertencia
            fecha_res = await safe_text(
                tab, base_xpath,
                "//div[div[contains(.,'Fecha de Resolución:')]]/div[contains(@class,'fleft')]"
            )

            if not fecha_res:
                fecha_res = await safe_text(
                    tab, base_xpath,
                    "//div[div[contains(.,'Fecha de Ingreso:')]]/div[contains(@class,'fleft')]"
                )
                downloadable = False

        # -----------------------------
        # PARSEO DE FECHA
        # -----------------------------
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
            except:
                logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_res}")

        # -----------------------------
        # DATOS
        # -----------------------------
        data["radicado"] = radicado
        data["cod_despacho_rama"] = cod_despacho_rama
        data["fecha"] = fecha_formateada
        data["actuacion_rama"] = await safe_text(
            tab, base_xpath,
            "//div[contains(.,'Acto:')]/following-sibling::div[contains(@class,'fleft')]"
        )
        data["anotacion_rama"] = await safe_text(
            tab, base_xpath,
            "//div[div[contains(.,'Sumilla:')]]/div[contains(@class,'fleft')]"
        )
        data["origen_datos"] = "CEJ_PERU"
        data["fecha_registro_tyba"] = fecha_registro_tyba
        data["downloadable"] = downloadable
        if downloadable:
            try:
                logger.info(f"⬇️ Descargando archivo panel {idx}")

                download_el = await tab.find(
                    xpath=f"{base_xpath}//a[contains(@class,'aDescarg')]",
                    timeout=5
                )

                # 🔑 Obtener href REAL
                href =  download_el.get_attribute("href")

                if not href:
                    raise Exception("No se pudo obtener href de descarga")

                # 🔥 FORZAR descarga navegando directo
                await tab.execute_script(f"""
                    window.location.href = "{href}";
                """)

                logger.info(f"✅ Navegando a URL de descarga (panel {idx})")

                # ⏳ esperar descarga real
                await asyncio.sleep(5)

            except Exception as e:
                logger.warning(
                    f"⚠️ No se pudo descargar archivo del panel {idx}: {e}"
                )



        resoluciones.append(data)

    try:
        jsons_dir = "output/jsons"
        os.makedirs(jsons_dir, exist_ok=True)

        file_path = f"{jsons_dir}/actuaciones.ndjson"

                # Append línea por línea (no se corrompe)
        with open(file_path, "a", encoding="utf-8") as f:
            for r in resoluciones:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        logger.info(f"📝 {len(resoluciones)} actuaciones agregadas a {file_path}")

    except Exception as e:
        logger.error(f"❌ Error guardando NDJSON: {e}")

    logger.info(f"✅ Total actuaciones extraídas: {len(resoluciones)}")
    return resoluciones

import json
async def get_actores_rama(tab: Tab, radicado: str) -> list[dict]:
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
        logger.info(f"✅ Actores extraídos: {len(actores)}")

        return actores

    except Exception as e:
        logger.error(
            f"❌ Error extrayendo actores CEJ | Radicado={radicado}: {e}",
            exc_info=True
        )
        return []



async def main():
    case_information={
        "nombre_completo": "ERICK JOEL ANAYA GALLARDO",
        "distrito_judicial": "", 
        "instancia": "",
        "especialidad": "",
        "annio": "", 
        "num_expediente": "", 
        "parte": "ANAYA GALLARDO",
        "radicado": "00144-2023-0-1814-JP-CI-02",
        "demandante": "BANCO INTERNACION DEL PERU INTERBANK", 
        "parte_demandante": "DEL PERU INTERBANK"

        }
    await scrapper( case_information)




async def _extract_actors_pydoll( tab:Tab, radicado):
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
                logger.warning("⚠️ No se encontraron sujetos procesales")
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
            carpeta = "output/jsons"
            os.makedirs(carpeta, exist_ok=True)

            file_path = f"{carpeta}/sujetos.ndjson"

            records = df.to_dict(orient="records")

            with open(file_path, "a", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

            logger.info(f"📝 {len(records)} sujetos agregados a {file_path}")

            return df

        except WaitElementTimeout:
            logger.warning("⚠️ No se encontró el elemento div.partesp")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ Error extrayendo sujetos procesales: {e}")
            return pd.DataFrame()


async def extract_reporte_expediente(tab: Tab, radicado):
    try:
        # 🔹 Esperar que cargue el grid del reporte
        await tab.find(
            xpath="//div[@id='gridRE']",
            timeout=10
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

        data = {
            "RADICADO_RAMA": radicado,
            "ESPECIALISTA_LEGAL": await get_text("Especialista Legal"),
            "FECHA_INICIO": await get_text("Fecha de Inicio"),
            "MATERIA": await get_text("Materia"),
            "ETAPA_PROCESAL": await get_text("Etapa Procesal"),
            "UBICACION": await get_text("Ubicación"),
            "ESPECIALIDAD": await get_text("Especialidad"),
            "ESTADO": await get_text("Estado"),
            "DISTRITO_JUDICIAL": await get_text("Distrito Judicial"),
            "ORIGEN_DATOS": "CEJ_PERU"
        }

        return data

    except Exception as e:
        logger.error(f"❌ Error extrayendo reporte del expediente: {e}")
        return {}




if __name__ == "__main__":
    asyncio.run(main())
