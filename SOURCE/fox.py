import csv
import os
import pdfplumber
import re
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Preformatted




# =============
# MAPA DE MESES
# =============
MONTH_MAP = {
    "01": "ENE.", "ENE": "ENE.", "ENERO": "ENE.",
    "02": "FEB.", "FEB": "FEB.", "FEBRERO": "FEB.",
    "03": "MAR.", "MAR": "MAR.", "MARZO": "MAR.",
    "04": "ABR.", "ABR": "ABR.", "ABRIL": "ABR.",
    "05": "MAY.", "MAY": "MAY.", "MAYO": "MAY.",
    "06": "JUN.", "JUN": "JUN.", "JUNIO": "JUN.",
    "07": "JUL.", "JUL": "JUL.", "JULIO": "JUL.",
    "08": "AGO.", "AGO": "AGO.", "AGOSTO": "AGO.",
    "09": "SEP.", "SEP": "SEP.", "SEPTIEMBRE": "SEP.",
    "10": "OCT.", "OCT": "OCT.", "OCTUBRE": "OCT.",
    "11": "NOV.", "NOV": "NOV.", "NOVIEMBRE": "NOV.",
    "12": "DIC.", "DIC": "DIC.", "DICIEMBRE": "DIC."
}



# ============================
# ORDENADOR DE FECHAS MM/YY
# ============================
def sort_by_month(rows):
    def key_func(item):
        date = item[0]
        mm, yy = date.split("/")
        return int("20" + yy), int(mm)

    return sorted(rows, key=key_func)


# =
# NATURAL SORTING
# =
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r"(\d+)", s)]


# =================
# ARCHIVO SNAPSHOT (scraper)
# =================
def is_snapshot_file(fn):
    # Los snapshots llevan _AAAA-MM.csv al final (los genera scraper.py)
    return bool(re.search(r"_\d{4}-\d{2}\.csv$", fn))


# ===================
# NORMALIZADOR FECHAS
# ===================
def normalize_date(date_raw):
    date_raw = date_raw.strip().upper()

    # Accept MM/YY or MM-YY
    if "/" in date_raw:
        mm, yy = date_raw.split("/")
    elif "-" in date_raw:
        mm, yy = date_raw.split("-")
    else:
        raise ValueError("Formato de fecha invalido")

    mm = mm.strip()
    yy = yy.strip()

    # If month is text (ENE, FEB, etc)
    if not mm.isdigit():
        mm = MONTH_MAP.get(mm.replace(".", ""), None)
        if not mm:
            raise ValueError("Mes invalido")
        for k, v in MONTH_MAP.items():
            if v == mm and k.isdigit():
                mm = k
                break

    if len(mm) == 1:
        mm = "0" + mm

    return f"{mm}/{yy}"


# =======================
# NORMALIZADOR DE NUMEROS
# =======================
def normalize_number(num_raw):
    num_raw = num_raw.strip().replace('"', "")

    # If it has both , and . → assume . = thousands
    if "," in num_raw and "." in num_raw:
        num_raw = num_raw.replace(".", "").replace(",", ".")
    else:
        num_raw = num_raw.replace(",", ".")

    return float(num_raw)


# ======================
# NORMALIZADOR DE SALIDA
# ======================
def format_money(val):
    s = f"{val:,.2f}"
    s = s.replace(",", "X")
    s = s.replace(".", ",")
    s = s.replace("X", ".")
    return "$" + s


# ============
# DIVISOR AUTO
# ============
def make_divider(header_line):
    return "-" * len(header_line)


# ===========================
# DIFF DE MESES CON CORRIENTE
# ===========================
def months_diff(date_str, ref=None):
    mm, yy = date_str.split("/")
    year = int("20" + yy)
    month = int(mm)

    ref = ref or datetime.now()
    return (ref.year - year) * 12 + (ref.month - month)


# ========================
# CORRECTOR DE ROOT FOLDER
# ========================
def get_base_dir():
    # If running from PyInstaller exe
    if getattr(sys, 'frozen', False):
        exe_path = os.path.dirname(sys.executable)
        # If exe is inside /dist, use its parent directory as base
        if os.path.basename(exe_path).lower() == "dist":
            return os.path.dirname(exe_path)
        return exe_path
    else:
        # Running from raw .py source. fox.py vive en SOURCE/, así que la raíz
        # del proyecto (donde viven input.txt, agendae.cfg, TABLAS/, PLANILLAS/,
        # ICON/) es la carpeta padre de SOURCE/. Todas las rutas de este módulo
        # se resuelven contra BASE_PATH.
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = get_base_dir()

# ============================
# LECTOR UNIVERSAL DE input.txt
# ============================
def read_input_file():
    INPUT_FILE = os.path.join(BASE_PATH, "input.txt")

    if not os.path.exists(INPUT_FILE):
        print("ERROR: No se encontró el archivo input.txt.")
        return None

    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) != 2:
                print("ERROR: Línea inválida en input.txt:", line)
                continue

            date_raw, value_raw = parts
            try:
                date = normalize_date(date_raw)
                value = normalize_number(value_raw)
            except ValueError:
                print("ERROR: Valor numérico inválido en input.txt:", line)
                continue

            rows.append((date, value))

    if not rows:
        print("ERROR: El archivo input.txt está vacío o es inválido.")
        return None

    # ORDENAR POR MES (VIEJO → NUEVO)
    return sort_by_month(rows)


# ================
# OUTPUT UNIVERSAL
# ================
def write_output(results, input_rows, output_name):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Preformatted
    import os

    SIDE_MARGIN = 10
    CE_FL_MARGIN = 12

    PLANILLAS_PATH = os.path.join(BASE_PATH, "PLANILLAS")

    if not os.path.exists(PLANILLAS_PATH):
        os.makedirs(PLANILLAS_PATH)

    OUTPUT_FILE = os.path.join(PLANILLAS_PATH, output_name + ".pdf")

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=SIDE_MARGIN * mm,
        rightMargin=SIDE_MARGIN * mm,
        topMargin= CE_FL_MARGIN * mm,
        bottomMargin= CE_FL_MARGIN * mm
    )

    styles = getSampleStyleSheet()
    mono_style = styles["Normal"]
    mono_style.fontName = "Courier"
    mono_style.fontSize = 11
    mono_style.leading = 10

    flow = []

    # =========================
    # NORMAL REPORT PAGES
    # =========================
    for line in results:
        flow.append(Preformatted(line, mono_style))

    # =========================
    # HIDDEN RELOAD PAGE
    # =========================
    flow.append(PageBreak())

    reload_lines = []
    reload_lines.append("#PDF_RELOAD_V1")
    reload_lines.append(f"ROWS={len(input_rows)}")
    reload_lines.append("")

    for date, value in input_rows:
        reload_lines.append(f"{date}|{value:.2f}")

    reload_block = "\n".join(reload_lines)
    flow.append(Preformatted(reload_block, mono_style))

    doc.build(flow)
    return OUTPUT_FILE



# =================
# CARGADOR DE DATOS
# =================
def load_input_from_pdf(pdf_path):

    if not os.path.exists(pdf_path):
        print("\nERROR: No se encontró el archivo PDF.")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        last_page = pdf.pages[-1]
        text = last_page.extract_text()

    if not text or "#PDF_RELOAD_V1" not in text:
        print("\nERROR: El PDF no es compatible con este programa.")
        return None

    lines = text.splitlines()

    data_lines = []
    for line in lines:
        line = line.strip()

        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("ROWS"):
            continue

        if "|" in line:
            data_lines.append(line)

    if not data_lines:
        print("\nERROR: No se encontraron datos válidos en el PDF.")
        return None

    rows = []
    for row in data_lines:
        date, value = row.split("|")
        value = value.replace(",", ".").strip()
        rows.append((date.strip(), float(value)))
    return rows




# ============================
# MODO DESDE TABLA (CSV)
# ============================
def get_csv_files():
    """Return list of available (non-snapshot) CSV paths relative to TABLAS/."""
    TABLAS_PATH = os.path.join(BASE_PATH, "TABLAS")
    if not os.path.exists(TABLAS_PATH):
        return []
    csv_files = []
    for raiz, _, archivos in os.walk(TABLAS_PATH):
        for f in archivos:
            if not f.lower().endswith(".csv"):
                continue
            if is_snapshot_file(f):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), TABLAS_PATH)
            csv_files.append(rel.replace(os.sep, "/"))
    return sorted(csv_files, key=natural_sort_key)


def from_tabla(input_rows, csv_rel_path, global_mult, output_name):
    TABLAS_PATH = os.path.join(BASE_PATH, "TABLAS")
    CSV_FILE = os.path.join(TABLAS_PATH, csv_rel_path)
    data = {}
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        years = headers[1:]
        for row in reader:
            month = row[0].strip()
            values = row[1:]
            data[month] = {}
            for year, val in zip(years, values):
                val = val.strip().replace('"', "")
                if not val:
                    continue
                val = val.replace(".", "").replace(",", ".")
                try:
                    data[month][year] = normalize_number(val)
                except ValueError:
                    pass
    calc_date  = datetime.now().strftime("%d/%m/%Y")
    tabla_name = os.path.splitext(os.path.basename(csv_rel_path))[0]
    results = []
    total_capital = 0.0
    total_interes = 0.0
    total_final   = 0.0
    results.append(f"Tabla: {tabla_name}")
    results.append(f"Fecha de calculo: {calc_date}")
    results.append("")
    results.append(
        f"{'':<5} | "
        f"{''  :>15} | "
        f"{''  :>6} | "
        f"{f'[{global_mult:.2f}]':>6} | "
        f"{''  :>15} | "
        f"{''  :>18}"
    )
    results.append(
        f"{'FECHA':<5} | "
        f"{'CAPITAL':>15} | "
        f"{'COEF':>6} | "
        f"{'MULT':>6} | "
        f"{'INTERES':>15} | "
        f"{'CAPITAL + INT':>18}"
    )
    results.append(make_divider(results[-1]))
    for date, capital in input_rows:
        mm, yy = date.split("/")
        year   = "20" + yy
        month  = MONTH_MAP.get(mm)
        if month not in data or year not in data[month]:
            results.append(f"{date:<7} | ERROR DE FECHA")
            continue
        coeficiente   = data[month][year]
        coef_con_mult = ((coeficiente - 1) * global_mult) + 1
        final   = capital * coef_con_mult
        interes = final - capital
        total_capital += capital
        total_interes += interes
        total_final   += final
        results.append(
            f"{date:<5} | "
            f"{format_money(capital):>15} | "
            f"{coeficiente:>6.3f} | "
            f"{coef_con_mult:>6.3f} | "
            f"{format_money(interes):>15} | "
            f"{format_money(final):>18}"
        )
    results.append(make_divider(results[-1]))
    results.append(
        f"{'TOTAL':<5} | "
        f"{format_money(total_capital):>15} | "
        f"{''  :>6} | "
        f"{''  :>6} | "
        f"{format_money(total_interes):>15} | "
        f"{format_money(total_final):>18}"
    )
    return write_output(results, input_rows, output_name)


# ============================
# MODO DESDE PORCENTAJE
# ============================
def from_percent(input_rows, base_percent, ref_date, output_name):
    results = []
    total_importe = 0.0
    total_interes = 0.0
    total_final   = 0.0
    results.append(
        f"{'FECHA':<5} | "
        f"{'CAPITAL':>15} | "
        f"{'%':>10} | "
        f"{'INTERES':>15} | "
        f"{'CAPITAL + INT':>17}"
    )
    results.append(make_divider(results[0]))
    for date, capital in input_rows:
        diff    = months_diff(date, ref_date)
        percent = diff * base_percent
        interes = capital * (percent / 100)
        final   = capital + interes
        total_importe += capital
        total_interes += interes
        total_final   += final
        results.append(
            f"{date:<5} | "
            f"{format_money(capital):>15} | "
            f"{percent:>9.2f}% | "
            f"{format_money(interes):>15} | "
            f"{format_money(final):>17}"
        )
    results.append(make_divider(results[0]))
    results.append(
        f"{'TOTAL':<5} | "
        f"{format_money(total_importe):>15} | "
        f"{''  :>10} | "
        f"{format_money(total_interes):>15} | "
        f"{format_money(total_final):>17}"
    )
    return write_output(results, input_rows, output_name)


# ============================
# MENÚ PRINCIPAL
# ============================
def main():
    from gui import run_app
    run_app()


# ============================
# PUNTO DE ENTRADA
# ============================
if __name__ == "__main__":
    main()
