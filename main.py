import io
import logging
import re
import time
from datetime import date, datetime

import ddddocr
import requests
import urllib3
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

urllib3.disable_warnings()

BASE_URL = "https://cej.pj.gob.pe/cej"

# Códigos de respuesta conocidos del servidor
RESP_CAPTCHA_WRONG = "-C"
RESP_PARTE_WRONG   = "-P"
RESP_PARTE_REQ     = "parte_req"
RESP_NO_EXISTE     = "-N"
RESP_SESSION_EXP   = "-S"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept-Language": "es-419,es;q=0.9",
    "Sec-Ch-Ua": '"Not-A.Brand";v="24", "Chromium";v="146"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

_ocr = ddddocr.DdddOcr(show_ad=False)


# ---------------------------------------------------------------------------
# Sesión
# ---------------------------------------------------------------------------

def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False
    resp = session.get(
        f"{BASE_URL}/forms/busquedaform.html",
        headers={
            **HEADERS,
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
        },
    )
    resp.raise_for_status()
    print(f"[+] Sesión iniciada. JSESSIONID: {session.cookies.get('JSESSIONID')}")
    return session


# ---------------------------------------------------------------------------
# CAPTCHA
# ---------------------------------------------------------------------------

def _intentar_ocr(img_bytes: bytes) -> str:
    text = _ocr.classification(img_bytes)
    return "".join(c for c in text.upper().strip() if c.isalnum())


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _variantes_preprocesado(raw: bytes):
    """
    Captcha CEJ: texto blanco/claro sobre fondo rojo oscuro, con una línea
    diagonal delgada cruzando los caracteres como anti-OCR.

    Estrategia clave: MedianFilter elimina la línea delgada (1-2px) porque
    los caracteres son gruesos y sobreviven el filtrado.
    """
    img_orig = Image.open(io.BytesIO(raw)).convert("RGB")
    variantes = []

    # --- base compartida: grises → invertir → x2 ---
    def base():
        g = img_orig.convert("L")
        g = ImageOps.invert(g)
        return g

    # V1: base + escalar x2 (sin más procesado — referencia)
    g = base()
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    variantes.append(_png(g))

    # V2: base + MedianFilter(3) para matar la línea diagonal delgada + x2
    g = base()
    g = g.filter(ImageFilter.MedianFilter(size=3))
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    variantes.append(_png(g))

    # V3: base + MedianFilter(3) + contraste fuerte + umbral bajo (60) + x2
    g = base()
    g = g.filter(ImageFilter.MedianFilter(size=3))
    g = ImageEnhance.Contrast(g).enhance(3.0)
    g = g.point(lambda p: 0 if p < 60 else 255)
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    variantes.append(_png(g))

    # V4: base + MedianFilter(3) + contraste + umbral medio (120) + x2
    g = base()
    g = g.filter(ImageFilter.MedianFilter(size=3))
    g = ImageEnhance.Contrast(g).enhance(2.5)
    g = g.point(lambda p: 0 if p < 120 else 255)
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    variantes.append(_png(g))

    # V5: canal verde (buen contraste texto blanco vs fondo rojo) + invertir + median + x2
    g = img_orig.split()[1]   # canal G
    g = ImageOps.invert(g)
    g = g.filter(ImageFilter.MedianFilter(size=3))
    g = ImageEnhance.Contrast(g).enhance(3.0)
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    variantes.append(_png(g))

    return variantes


def solve_captcha(session: requests.Session, save_path: str = None) -> str:
    """
    Método principal: lee el captcha desde el endpoint de audio /cej/xyhtml.
    El servidor devuelve HTML con un <input id="1zirobotz0" value="XXXX">
    que contiene el texto exacto del captcha — el mismo que el botón de audio
    pronuncia con Web Speech API. Preciso al 100%, sin OCR.
    Fallback a OCR si el endpoint falla.
    """
    try:
        # 1. Cargar imagen para que el servidor genere el captcha en sesión
        session.get(
            f"{BASE_URL}/Captcha.jpg?{int(time.time() * 1000)}",
            headers={"Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"},
        ).raise_for_status()

        # 2. Leer el valor desde el endpoint de audio
        resp = session.get(
            f"{BASE_URL}/xyhtml",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "*/*",
                "Referer": f"{BASE_URL}/forms/busquedaform.html",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
            },
        )
        resp.raise_for_status()
        match = re.search(r'id=["\']1zirobotz0["\'][^>]*value=["\']([^"\']+)["\']', resp.text)
        if not match:
            match = re.search(r'value=["\']([^"\']+)["\'][^>]*id=["\']1zirobotz0["\']', resp.text)
        if match and match.group(1).upper() != "NULL":
            texto = "".join(c for c in match.group(1).upper().strip() if c.isalnum())
            print(f"[+] CAPTCHA (audio): {texto!r}")
            return texto
        print("[!] xyhtml devolvió NULL, usando OCR...")
    except Exception as e:
        print(f"[!] Endpoint audio falló ({e}), usando OCR como fallback...")

    return _solve_captcha_ocr(session, save_path)


def _solve_captcha_ocr(session: requests.Session, save_path: str = None) -> str:
    """Fallback OCR cuando /cej/xyhtml no está disponible."""
    raw = session.get(
        f"{BASE_URL}/Captcha.jpg?{int(time.time() * 1000)}",
        headers={"Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"},
    ).content

    if save_path:
        with open(save_path, "wb") as f:
            f.write(raw)

    variantes = _variantes_preprocesado(raw)

    if save_path:
        for i, v in enumerate(variantes):
            p = save_path.replace(".", f"_v{i+1}.")
            with open(p, "wb") as f:
                f.write(v)
        print(f"[+] CAPTCHA + {len(variantes)} variantes guardadas en: {save_path}")

    candidatos = [_intentar_ocr(v) for v in variantes]
    texto = next((t for t in candidatos if len(t) == 4), max(candidatos, key=len))
    print(f"[+] CAPTCHA (OCR) candidatos: {candidatos}  →  elegido: {texto!r}")
    return texto


# ---------------------------------------------------------------------------
# Internos
# ---------------------------------------------------------------------------

def _validar(session, payload_valida, referer, label, max_intentos):
    """
    Llama a ValidarFiltrosCodigo.htm hasta resolver el CAPTCHA.
    Devuelve el número de resultados (int) o None si no hay expediente.
    """
    for intento in range(1, max_intentos + 1):
        captcha = solve_captcha(session)
        payload_valida["codigoCaptcha"] = captcha

        r = session.post(
            f"{BASE_URL}/forms/ValidarFiltrosCodigo.htm",
            data=payload_valida,
            headers={
                **HEADERS,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://cej.pj.gob.pe",
                "Referer": referer,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
            },
        )
        r.raise_for_status()
        data = r.text.strip()
        print(f"[Intento {intento}] {label}: {data[:200]}")

        if len(data) > 50 or data.startswith(RESP_CAPTCHA_WRONG) or "captcha" in data.lower():
            print(f"[!] CAPTCHA incorrecto, reintentando ({intento}/{max_intentos})...")
            time.sleep(1)
            continue
        elif data == RESP_SESSION_EXP:
            raise RuntimeError("Sesión expirada — crea una nueva sesión")
        elif data in (RESP_PARTE_REQ, RESP_PARTE_WRONG):
            raise ValueError(f"Parte inválida o requerida (respuesta: {data!r})")
        elif data == RESP_NO_EXISTE:
            print("[!] No existe expediente con esos datos.")
            return None

        if data.lstrip("-").isdigit():
            return int(data)

        # Respuesta inesperada: devolver tal cual para diagnóstico
        return data

    raise RuntimeError("No se pudo resolver el CAPTCHA tras varios intentos")


def _fetch_resultados(session, cod_expediente, cod_anio, cod_distprov,
                      cod_organo, cod_especialidad, cod_instancia, cod_incidente):
    """POST final a busquedacodform.html que devuelve el HTML con los resultados."""
    resp = session.post(
        f"{BASE_URL}/forms/busquedacodform.html",
        data={
            "cod_expediente": cod_expediente,
            "cod_anio": cod_anio,
            "cod_incidente": cod_incidente,
            "cod_distprov": cod_distprov,
            "cod_organo": cod_organo,
            "cod_especialidad": cod_especialidad,
            "cod_instancia": cod_instancia,
        },
        headers={
            **HEADERS,
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Origin": "https://cej.pj.gob.pe",
            "Referer": f"{BASE_URL}/forms/busquedaform.html",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        },
        allow_redirects=True,
    )
    resp.raise_for_status()
    print(f"[+] busquedacodform → {len(resp.text)} bytes  URL: {resp.url}")
    return resp.text


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def buscar_por_filtros(
    session: requests.Session,
    cod_expediente: str,
    cod_anio: str,
    cod_distprov: str,
    cod_organo: str,
    cod_especialidad: str,
    cod_instancia: str,
    parte: str,
    cod_incidente: str = "0",
    max_intentos: int = 5,
):
    """Flujo: ValidarFiltrosCodigo.htm → busquedacodform.html"""
    payload = {
        "cod_expediente": cod_expediente,
        "cod_anio": cod_anio,
        "cod_distprov": cod_distprov,
        "cod_organo": cod_organo,
        "cod_especialidad": cod_especialidad,
        "cod_instancia": cod_instancia,
        "codigoCaptcha": "",          # se rellena en _validar()
        "cod_incidente": cod_incidente,
        "parte": parte.upper(),
        "navegador": "Chrome--146",
        "divKcha": "0",
        "sCUJ": "",
    }
    n = _validar(session, payload, f"{BASE_URL}/forms/busquedaform.html",
                 "ValidarFiltros", max_intentos)
    if n is None or not isinstance(n, int):
        return n

    return _fetch_resultados(session, cod_expediente, cod_anio, cod_distprov,
                              cod_organo, cod_especialidad, cod_instancia, cod_incidente)


def buscar_por_codigo(
    session: requests.Session,
    cod_expediente: str,
    cod_anio: str,
    cod_distprov: str,
    cod_organo: str,
    cod_especialidad: str,
    cod_instancia: str,
    parte: str,
    cod_incidente: str = "0",
    max_intentos: int = 5,
):
    """Flujo: ValidarFiltrosCodigo.htm → busquedacodform.html"""
    payload = {
        "cod_expediente": cod_expediente,
        "cod_anio": cod_anio,
        "cod_distprov": cod_distprov,
        "cod_organo": cod_organo,
        "cod_especialidad": cod_especialidad,
        "cod_instancia": cod_instancia,
        "codigoCaptcha": "",
        "cod_incidente": cod_incidente,
        "parte": parte.upper(),
        "navegador": "Chrome--146",
        "divKcha": "0",
        "sCUJ": "",
    }
    n = _validar(session, payload, f"{BASE_URL}/forms/busquedaform.html",
                 "ValidarFiltros(código)", max_intentos)
    if n is None or not isinstance(n, int):
        return n

    return _fetch_resultados(session, cod_expediente, cod_anio, cod_distprov,
                              cod_organo, cod_especialidad, cod_instancia, cod_incidente)


# ---------------------------------------------------------------------------
# Parseo del HTML de resultados
# ---------------------------------------------------------------------------

def parse_case_report(soup: BeautifulSoup) -> tuple[dict, str]:
    grid = soup.find("div", id="gridRE")
    if not grid:
        logger.warning("No se encontró div#gridRE")
        return {}, ""

    def get_text(label: str) -> str:
        celda = grid.find(
            lambda tag: tag.name == "div"
            and "celdaGridN" in tag.get("class", [])
            and label in tag.get_text(strip=True)
        )
        if not celda:
            return ""
        siguiente = celda.find_next_sibling("div")
        return siguiente.get_text(strip=True).replace("\xa0", "") if siguiente else ""

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
    despacho = get_text("Órgano Jurisdiccional")
    return data, despacho


def parse_actores(soup: BeautifulSoup) -> list[dict]:
    filas = soup.select("#collapseTwo .panelGrupo .partes")
    if len(filas) <= 1:
        logger.warning("No se encontraron actores en el panel.")
        return []

    actores = []
    for fila in filas[1:]:
        def get(selector):
            el = fila.select_one(selector)
            return el.get_text(strip=True) if el else ""

        razon_social = get(".cNombresD")
        nombres  = get(".cNombD")
        ap_pat   = get(".cApPaD")
        ap_mat   = get(".cApMaD")
        nombre   = razon_social or " ".join(filter(None, [nombres, ap_pat, ap_mat]))

        actores.append({
            "tipo_sujeto":  get(".cPartTip.cPartI"),
            "nombre_actor": nombre,
        })
    return actores


def _parse_fecha(fecha_str: str) -> date | None:
    for fmt in ("%d/%m/%Y", "%d/%m/%Y %H:%M", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    logger.warning(f"No se pudo parsear fecha: {fecha_str!r}")
    return None


def parse_actions(soup: BeautifulSoup, radicado: str, cod_despacho: str) -> tuple[list[dict], list[dict]]:
    panels = soup.select("div[id^='pnlSeguimiento']")
    if not panels:
        logger.warning("No se encontraron paneles de seguimiento.")
        return [], []

    todas, descargables = [], []

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
            sib = target.find_next_sibling("div")
            return sib.get_text(strip=True).replace("\xa0", "") if sib else ""

        msg_el = panel.find("div", class_="sinResol")
        if msg_el:
            fleft = panel.find("div", class_="fleft")
            fecha_raw = fleft.get_text(strip=True) if fleft else ""
        else:
            fecha_raw = get_field("Fecha de Resolución:") or get_field("Fecha de Ingreso:")

        fecha_obj = _parse_fecha(fecha_raw) if fecha_raw else None
        fecha_fmt = fecha_obj.strftime("%d-%m-%Y") if fecha_obj else None
        fecha_tyba = (
            fecha_obj.strftime("%d-%m-%Y 00:00:00") if fecha_obj else "00-00-0000 00:00:00"
        )

        data = {
            "radicado":            radicado,
            "cod_despacho_rama":   cod_despacho,
            "fecha":               fecha_fmt,
            "actuacion_rama":      get_field("Acto:"),
            "anotacion_rama":      get_field("Sumilla:"),
            "origen_datos":        "CEJ_PERU",
            "fecha_registro_tyba": fecha_tyba,
        }

        vacios = [k for k, v in data.items() if not v]
        if vacios:
            logger.warning(f"Panel {panel_id} omitido — campos vacíos: {vacios}")
            continue

        todas.append(data)

        boton = panel.find("div", class_="dBotonDesc")
        if boton:
            a = boton.find("a", class_="aDescarg")
            href = a["href"] if a else ""
            nid_match = re.search(r"nid=([^&]+)", href)
            nid = nid_match.group(1) if nid_match else ""
            descargables.append({**data, "panel_id": panel_id, "nid": nid})

    logger.info(f"Actuaciones: {len(todas)} total | {len(descargables)} con descarga")
    return todas, descargables


def filter_new_actions(todas: list[dict], existing: set[tuple]) -> list[dict]:
    """
    Filtra actuaciones que NO existen aún.
    `existing` = set de (radicado, fecha_str) ya presentes en BD.
    Calcula el consecutivo como posición dentro del mismo (radicado, fecha).
    """
    consecutivos: dict[tuple, int] = {}
    nuevas = []

    for action in todas:
        key = (action["radicado"], action["fecha"])
        consecutivos[key] = consecutivos.get(key, 0) + 1
        consecutivo = consecutivos[key]

        if key in existing:
            logger.info(f"Ya existe → {key} consecutivo={consecutivo}")
            continue

        nuevas.append({**action, "consecutivo": consecutivo})

    logger.info(f"Nuevas actuaciones: {len(nuevas)}/{len(todas)}")
    return nuevas


def parse_nro_registros(html: str) -> list[str]:
    """Extrae los nroRegistro del HTML de lista de resultados."""
    soup = BeautifulSoup(html, "html.parser")
    registros = []
    for inp in soup.select("input[name='nroRegistro']"):
        val = inp.get("value", "").strip()
        if val:
            registros.append(val)
    logger.info(f"nroRegistro encontrados: {registros}")
    return registros


def fetch_detalle(session: requests.Session, nro_registro: str) -> str:
    """POST a detalleform.html para obtener el HTML de detalle del expediente."""
    resp = session.post(
        f"{BASE_URL}/forms/detalleform.html",
        data={"nroRegistro": nro_registro},
        headers={
            **HEADERS,
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Origin": "https://cej.pj.gob.pe",
            "Referer": f"{BASE_URL}/forms/busquedacodform.html",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        },
        allow_redirects=True,
    )
    resp.raise_for_status()
    logger.info(f"detalleform → {len(resp.text)} bytes")
    return resp.text


def parse_html(html_detalle: str, radicado: str) -> dict:
    """Parsea el HTML de detalle del expediente."""
    soup = BeautifulSoup(html_detalle, "html.parser")
    case_report, despacho = parse_case_report(soup)
    actores = parse_actores(soup)
    todas, descargables = parse_actions(soup, radicado, despacho)
    return {
        "case_report":  case_report,
        "despacho":     despacho,
        "actores":      actores,
        "todas":        todas,
        "descargables": descargables,
    }


# ---------------------------------------------------------------------------
# Descarga de documentos
# ---------------------------------------------------------------------------

MIME_EXT = {
    "application/pdf":                                                      ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword":                                                   ".doc",
    "application/octet-stream":                                             ".bin",
}

def download_documento(session: requests.Session, nid: str, output_dir: str, filename_base: str) -> str | None:
    """Descarga el documento con el nid dado y lo guarda en output_dir."""
    url = f"{BASE_URL}/forms/documentoD.html?nid={nid}"
    resp = session.get(
        url,
        headers={
            **HEADERS,
            "Accept": "application/pdf,application/octet-stream,*/*",
            "Referer": f"{BASE_URL}/forms/detalleform.html",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        },
        stream=True,
    )
    resp.raise_for_status()

    mime = resp.headers.get("Content-Type", "").split(";")[0].strip()
    ext  = MIME_EXT.get(mime, ".bin")

    import os
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{filename_base}{ext}")

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Descargado → {filepath}  ({mime})")
    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    session = get_session()

    # Warm-up: sincroniza el captcha de sesión con el servidor
    solve_captcha(session)

    resultado = buscar_por_filtros(
        session=session,
        cod_expediente="03394",
        cod_anio="2014",
        cod_distprov="0701",
        cod_organo="JR",
        cod_especialidad="CI",
        cod_instancia="01",
        parte="GUILLERMO ARTURO TOMASEVICH HERNANDO",
    )
    if not isinstance(resultado, str):
        print("Sin resultado HTML.")
    else:
        radicado = "03394-2014-0-0701-JR-CI-01"

        # Paso 3: extraer nroRegistro de la lista y pedir el detalle
        registros = parse_nro_registros(resultado)
        if not registros:
            print("No se encontraron expedientes en la lista.")
        else:
            for nro in registros:
                html_detalle = fetch_detalle(session, nro)
                datos = parse_html(html_detalle, radicado)

                print(f"\n=== Reporte del caso (nroRegistro={nro}) ===")
                for k, v in datos["case_report"].items():
                    print(f"  {k}: {v}")
                print(f"  Despacho: {datos['despacho']}")

                print("\n=== Actores ===")
                for a in datos["actores"]:
                    print(f"  [{a['tipo_sujeto']}] {a['nombre_actor']}")

                print(f"\n=== Actuaciones ({len(datos['todas'])} total) ===")
                for act in datos["todas"]:
                    print(f"  {act['fecha']} | {act['actuacion_rama']} | {act['anotacion_rama'][:60]}")

                print(f"\n=== Descargables ({len(datos['descargables'])}) ===")
                for d in datos["descargables"]:
                    print(f"  panel={d['panel_id']} fecha={d['fecha']} {d['actuacion_rama']}")

                nuevas = filter_new_actions(datos["descargables"], existing=set())
                print(f"\n=== Nuevas a descargar: {len(nuevas)} ===")

                for accion in nuevas:
                    nid  = accion.get("nid", "")
                    if not nid:
                        logger.warning(f"Sin nid para {accion['panel_id']}, omitiendo.")
                        continue
                    nombre = f"{radicado}_{accion['fecha']}_{accion['panel_id']}"
                    download_documento(session, nid, output_dir="descargas", filename_base=nombre)
