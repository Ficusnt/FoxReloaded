#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper.py — Actualiza las tablas de FoxCapital desde agendae.com.ar.

Lee credenciales de agendae.cfg y las URLs a actualizar de TABLAS/config.txt.
Requiere: requests y beautifulsoup4.

Uso directo:
    python scraper.py
O desde el menú de FoxCapital (opción 0).
"""
import csv
import os
import re
import sys
import time

import requests

# ---------------------------------------------------------------------------
# RUTA BASE (robusta: .py suelto, exe PyInstaller en dist/, etc.)
# ---------------------------------------------------------------------------
def get_base_dir():
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        if os.path.basename(exe_dir).lower() == "dist":
            return os.path.dirname(exe_dir)
        return exe_dir
    # En modo fuente, scraper.py vive en SOURCE/: la raíz del proyecto (donde
    # están agendae.cfg y TABLAS/) es la carpeta padre de SOURCE/.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_PATH = get_base_dir()
CONFIG_CFG = os.path.join(BASE_PATH, "agendae.cfg")
TABLAS_PATH = os.path.join(BASE_PATH, "TABLAS")
TABLAS_CONFIG = os.path.join(TABLAS_PATH, "config.txt")

# ---------------------------------------------------------------------------
# LOGIN EN agendae.com.ar (endpoint AJAX _login.aspx)
# ---------------------------------------------------------------------------
_LOGIN_ENDPOINT = "_login.aspx"


def _nueva_sesion():
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0 Safari/537.36"),
    })
    return s


def login(session, base_url, usuario, password):
    """Autentica via el endpoint AJAX del sitio (_login.aspx).

    El servidor responde con una cadena que empieza con "OK" si el login
    fue exitoso, o un mensaje de error en caso contrario.
    """
    url = base_url.rstrip("/") + "/" + _LOGIN_ENDPOINT
    data = {
        "accion": "LOGIN",
        "usuario": usuario,
        "password": password,
        "entidad": "",
    }
    r = session.post(url, data=data, timeout=30)
    r.raise_for_status()
    resp = r.text.strip()
    if not resp.startswith("OK"):
        raise requests.RequestException(
            f"Login rechazado por el servidor: {resp!r}")


def tiene_acceso(session, url):
    """True si al pedir la página no nos rebota a noacceso1.aspx."""
    try:
        r = session.get(url, timeout=30)
    except requests.RequestException:
        return False
    return "noacceso" not in (r.url or "")


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
def leer_configuracion():
    if not os.path.exists(TABLAS_CONFIG):
        raise FileNotFoundError(
            f"No se encontró {TABLAS_CONFIG}. Definí las tablas a actualizar.")

    retencion = 6
    tablas = []  # [{"name": str, "url": str}]

    with open(TABLAS_CONFIG, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if not key or not val:
                continue
            if re.match(r"^retencion$", key, re.I):
                try:
                    retencion = int(val)
                except ValueError:
                    pass
                continue
            if val.lower().startswith("http"):
                tablas.append({"name": key, "url": val})

    if not tablas:
        raise ValueError("config.txt no tiene tablas configuradas.")

    return retencion, tablas


def leer_credenciales():
    if not os.path.exists(CONFIG_CFG):
        raise FileNotFoundError(
            f"No se encontró {CONFIG_CFG}. Crealo con una sección [agendae] "
            f"que tenga usuario / password / url.")

    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_CFG, encoding="utf-8")
    if not cfg.has_section("agendae"):
        raise ValueError("agendae.cfg debe tener una sección [agendae].")
    sec = cfg["agendae"]
    usuario = sec.get("usuario", "").strip()
    password = sec.get("password", "").strip()
    url = sec.get("url", "https://www.agendae.com.ar/").strip()
    if not usuario or not password:
        raise ValueError("Faltan usuario/password en agendae.cfg.")
    return usuario, password, url


# ---------------------------------------------------------------------------
# MESES / NÚMEROS
# ---------------------------------------------------------------------------
MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
         "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]


def normalizar_mes(texto):
    up = re.sub(r"[^A-Z]", "", texto.upper())
    for abbr in MESES:
        if up.startswith(abbr):
            return abbr
    return None


def parsear_numero_es(s):
    s = (s or "").strip().replace('"', "")
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def formatear_coef(v):
    if v is None:
        return ""
    return f"{v:.3f}".replace(".", ",")


# ---------------------------------------------------------------------------
# PARSEO DE LA TABLA via JSON (_back.aspx)
# ---------------------------------------------------------------------------
_BACK_ENDPOINT = "_back.aspx"


def _extraer_year(celda):
    """True si la celda es un año de 4 dígitos entre 1990 y 2100."""
    if re.fullmatch(r"\d{4}", str(celda)) and 1990 <= int(celda) <= 2100:
        return int(celda)
    return None


def fetch_tabla_json(session, base_url, page_url, idct):
    """Llama a _back.aspx y retorna la matríz {mes: {año: valor}}.

    Requiere que la session ya esté autenticada y que page_url haya
    sido visitada (establece el Referer correcto).
    """
    import json
    url = base_url.rstrip("/") + "/" + _BACK_ENDPOINT
    data = {
        "page": 1,
        "pageLimit": 0,
        "searchRecord": "",
        "sortName": "",
        "sortOrder": "",
        "tipoEntidad": "COEFICIENTES",
        "exportar": "",
        "from_admin": "N",
        "idct": idct,
    }
    r = session.post(url, data=data,
                     headers={"Referer": page_url,
                              "X-Requested-With": "XMLHttpRequest"},
                     timeout=30)
    r.raise_for_status()
    resp_text = r.text.strip()
    if resp_text.startswith("ERROR"):
        raise ValueError(f"_back.aspx devolvió error: {resp_text!r}")
    try:
        payload = json.loads(resp_text)
    except ValueError:
        raise ValueError("_back.aspx no devolvió JSON válido")

    headings = payload["dt"]["headings"]   # ["Mes", "2026", "2025", ...]
    rows     = payload["dt"]["data"]        # [["ENE.", "1,212", ...], ...]

    years = [(idx, int(h)) for idx, h in enumerate(headings)
             if _extraer_year(h) is not None]
    if not years:
        raise ValueError("el JSON no contiene columnas de año")

    matrix = {}
    for row in rows:
        if not row:
            continue
        mes = normalizar_mes(row[0]) if row[0] else None
        if mes is None:
            continue
        entry = matrix.setdefault(mes, {})
        for idx, year in years:
            if idx < len(row):
                val = parsear_numero_es(row[idx])
                if val is not None:
                    entry[year] = val

    if not matrix:
        raise ValueError("el JSON no contiene filas de meses")
    return matrix


# ---------------------------------------------------------------------------
# LECTURA / ESCRITURA DE ARCHIVOS (formato: Mes,2026,2025,...)
# ---------------------------------------------------------------------------
def _representacion_de_data(data):
    best = None
    for mes, entries in data.items():
        for year, val in entries.items():
            if val is None:
                continue
            key = (int(year), MESES.index(mes))
            if best is None or key > best:
                best = key
    if best:
        return f"{best[0]}-{best[1] + 1:02d}"
    return None


def leer_representacion(ruta):
    """Último (año-mes) con dato presente en un CSV ya guardado. None si no aplica."""
    try:
        with open(ruta, newline="", encoding="utf-8") as f:
            rd = csv.reader(f)
            header = next(rd, None)
            if not header or header[0].strip() != "Mes":
                return None
            years = [int(y) for y in header[1:] if _extraer_year(y.strip())]
            best = None
            for row in rd:
                mes = normalizar_mes(row[0]) if row else None
                if not mes:
                    continue
                for year, val in zip(years, row[1:]):
                    if parsear_numero_es(val) is not None:
                        key = (year, MESES.index(mes))
                        if best is None or key > best:
                            best = key
            if best:
                return f"{best[0]}-{best[1] + 1:02d}"
    except (OSError, ValueError):
        pass
    return None


def folder_de_nombre(name):
    """Carpeta inferida del prefijo antes del primer '_'. NBSF_ACT_CAP -> NBSF"""
    return name.split("_", 1)[0].upper()


def generar_csv(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    years = sorted({y for e in data.values() for y in e}, reverse=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Mes"] + [str(y) for y in years])
        for mes in MESES:
            e = data.get(mes, {})
            w.writerow([mes + "."] + [formatear_coef(e.get(y)) for y in years])


def archivos_snapshot(directory, name):
    pat = re.compile(r"^" + re.escape(name) + r"_(\d{4})-(\d{2})\.csv$")
    out = []
    if os.path.isdir(directory):
        for fn in os.listdir(directory):
            m = pat.match(fn)
            if m:
                out.append((m.group(1) + "-" + m.group(2), os.path.join(directory, fn)))
    return out


def aplicar_retencion(directory, name, retencion):
    snaps = sorted(archivos_snapshot(directory, name), key=lambda t: t[0], reverse=True)
    for _, ruta in snaps[retencion:]:
        try:
            os.remove(ruta)
            print(f"   (prune) {os.path.basename(ruta)}")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# ACCIÓN PRINCIPAL
# ---------------------------------------------------------------------------
def run_scrape():
    print("\n[Actualizar tablas de agendae.com.ar]")

    retencion, tablas = leer_configuracion()
    usuario, password, base_url = leer_credenciales()

    session = _nueva_sesion()
    print("Iniciando sesión...")
    try:
        login(session, base_url, usuario, password)
    except requests.RequestException as e:
        print(f"ERROR de red al iniciar sesión: {e}")
        return False

    if not tiene_acceso(session, tablas[0]["url"]):
        print("ERROR: no se pudo acceder a las tablas "
              "(¿credenciales inválidas o sesión no iniciada?).")
        return False

    print(f"Retención de snapshots: {retencion} mes(es).\n")

    for t in tablas:
        name, url = t["name"], t["url"]
        folder = folder_de_nombre(name)
        print(f"- {folder}/{name}.csv  <-  {url}")

        # Extraer idct del query string (?t=42)
        m = re.search(r"[?&]t=(\d+)", url)
        if not m:
            print("   (URL sin parámetro ?t=N, se omite)")
            continue
        idct = int(m.group(1))

        try:
            # Visitar la página primero para fijar el Referer y el estado de sesión
            rp = session.get(url, timeout=30)
            rp.raise_for_status()
            if "noacceso" in (rp.url or ""):
                print("   (sin acceso) se omite.")
                continue
            data = fetch_tabla_json(session, base_url, url, idct)
        except requests.RequestException as e:
            print(f"   (error de red) {e}")
            continue
        except ValueError as e:
            print(f"   (no se pudo parsear) {e}")
            continue

        if not data:
            print("   (sin datos) se omite.")
            continue

        directory = os.path.join(TABLAS_PATH, folder)
        current_path = os.path.join(directory, name + ".csv")
        nuevo_mes = _representacion_de_data(data)

        if os.path.exists(current_path):
            viejo_mes = leer_representacion(current_path)
            if viejo_mes and viejo_mes != nuevo_mes:
                snap_path = os.path.join(directory, f"{name}_{viejo_mes}.csv")
                try:
                    os.replace(current_path, snap_path)
                    print(f"   snapshot -> {os.path.basename(snap_path)}")
                except OSError as e:
                    print(f"   (error al crear snapshot) {e}")

        generar_csv(current_path, data)
        print(f"   guardado {folder}/{name}.csv")
        aplicar_retencion(directory, name, retencion)
        time.sleep(1.0)

    print("\nProceso de actualización finalizado.")
    return True


if __name__ == "__main__":
    run_scrape()