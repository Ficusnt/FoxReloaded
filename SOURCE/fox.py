import csv
import os
import pdfplumber
import re
import sys
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle,
)




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
# DIFF DE MESES CON CORRIENTE
# ============
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


def write_input_file(rows):
    """Write (date, capital) pairs to input.txt for crash recovery."""
    INPUT_FILE = os.path.join(BASE_PATH, "input.txt")
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        for date, value in rows:
            f.write(f"{date} {value:g}\n")


# ================
# OUTPUT UNIVERSAL
# ================

# -- Palette --
_CLR_DARK   = colors.HexColor("#1a1a2e")
_CLR_GREY_L = colors.HexColor("#f5f5f5")
_CLR_GREY_B = colors.HexColor("#e8eaf6")
_CLR_GREY_G = colors.HexColor("#cccccc")
_CLR_RED    = colors.HexColor("#c0392b")
_CLR_WHITE  = colors.white

# -- Styles --
_TITLE_STYLE = ParagraphStyle(
    "ReportTitle", fontName="Helvetica-Bold", fontSize=14,
    leading=17, spaceAfter=2, textColor=_CLR_DARK,
)
_META_STYLE = ParagraphStyle(
    "ReportMeta", fontName="Helvetica", fontSize=9,
    leading=11, spaceAfter=1, textColor=colors.HexColor("#666666"),
)
_HDR_MULTI = ParagraphStyle(
    "HeaderMulti", fontName="Helvetica-Bold", fontSize=9,
    leading=11, textColor=colors.white,
)
def _col_widths(headers, rows, totals, avail_w):
    """Proportional column widths based on max character count per column.

    Uses Courier metrics (fixed-width) so string-length ≈ rendered width.
    """
    n = len(headers)
    max_c = [max(len(line) for line in str(h).split("\n")) for h in headers]
    all_rows = [headers] + rows
    if totals:
        all_rows.append(totals)
    for row in all_rows:
        for i, cell in enumerate(row):
            if i < n:
                max_c[i] = max(max_c[i], len(str(cell)))
    max_c = [c + 4 for c in max_c]          # padding
    total = sum(max_c) or 1
    return [(c / total) * avail_w for c in max_c]


def write_output(report, input_rows, output_name):
    """Build a PDF from a structured *report* dict.

    report keys
    -----------
    title   : str          – heading
    meta    : list[str]    – subtitle lines (calc date, multiplier, …)
    headers : list[str]    – column headers
    rows    : list[list]   – data cells (pre-formatted strings)
    totals  : list | None  – optional totals row
    align   : list[str]    – per-col "l" / "r" / "c"
    errors  : dict[int,str]– row-index → message (rendered in red)
    """
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
        topMargin=CE_FL_MARGIN * mm,
        bottomMargin=CE_FL_MARGIN * mm,
    )

    flow = []

    # ── Title / meta ──
    flow.append(Paragraph(report.get("title", ""), _META_STYLE))
    for line in report.get("meta", []):
        flow.append(Paragraph(line, _META_STYLE))
    flow.append(Spacer(1, 8))

    # ── Table ──
    headers = report["headers"]
    data_rows = report["rows"]
    totals = report.get("totals")
    align = report.get("align", ["l"] * len(headers))
    errors = report.get("errors", {})

    # Render multi-line header cells (e.g. "MULT\n[1.50]") as stacked Paragraphs.
    rendered_headers = []
    for ci, h in enumerate(headers):
        if isinstance(h, str) and "\n" in h:
            anchor = {"l": TA_LEFT, "c": TA_CENTER, "r": TA_RIGHT}.get(align[ci], TA_RIGHT)
            ps = ParagraphStyle("hdr", parent=_HDR_MULTI, alignment=anchor)
            rendered_headers.append(Paragraph(h.replace("\n", "<br/>"), ps))
        else:
            rendered_headers.append(h)

    table_data = [rendered_headers] + data_rows
    if totals:
        table_data.append(totals)

    avail_w = A4[0] - (SIDE_MARGIN * mm * 2)
    col_widths = _col_widths(headers, data_rows, totals, avail_w)

    tbl = Table(table_data, colWidths=col_widths, hAlign="LEFT")

    cmds = [
        # Header band
        ("BACKGROUND",  (0, 0), (-1, 0), _CLR_DARK),
        ("TEXTCOLOR",   (0, 0), (-1, 0), _CLR_WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("TOPPADDING",  (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),

        # Data cells
        ("FONTNAME",    (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("TOPPADDING",  (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),

        # Grid
        ("GRID",        (0, 0), (-1, -1), 0.5, _CLR_GREY_G),
        ("LINEBELOW",   (0, 0), (-1, 0), 1, _CLR_DARK),
    ]

    # Alternating row shading
    for i in range(2, len(table_data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), _CLR_GREY_L))

    # Per-column alignment
    for ci, a in enumerate(align):
        anchor = "RIGHT" if a == "r" else ("CENTER" if a == "c" else "LEFT")
        cmds.append(("ALIGN", (ci, 0), (ci, -1), anchor))

    # Totals row
    if totals:
        ti = len(table_data) - 1
        cmds.append(("FONTNAME",    (0, ti), (-1, ti), "Courier-Bold"))
        cmds.append(("LINEABOVE",   (0, ti), (-1, ti), 1, _CLR_DARK))
        cmds.append(("BACKGROUND",  (0, ti), (-1, ti), _CLR_GREY_B))

    # Error cells → red
    for ri in errors:
        actual = ri + 1          # +1 for header
        if actual < len(table_data):
            cmds.append(("TEXTCOLOR", (0, actual), (-1, actual), _CLR_RED))

    tbl.setStyle(TableStyle(cmds))
    flow.append(tbl)

    doc.build(flow)
    return OUTPUT_FILE



# =================
# CARGADOR DE DATOS
# =================
def load_input_from_pdf(pdf_path):
    """Read back the date/capital rows from the visible table of a generated PDF.

    Parses the FECHA + CAPITAL columns of the pretty report (the same layout
    produced by both from_tabla and from_percent). Rows that can't be parsed
    (e.g. an "ERROR DE FECHA" row with no capital) come back as ("0/0", 0.0) so
    the position is preserved and the user can spot where the problem row was.
    """

    if not os.path.exists(pdf_path):
        print("\nERROR: No se encontró el archivo PDF.")
        return None

    cells = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
            })
            if not table:
                continue
            cells.extend(table)

    if not cells:
        print("\nERROR: No se encontraron datos válidos en el PDF.")
        return None

    data = []
    for row in cells:
        if not row:
            continue
        date_cell = (row[0] or "").strip()
        cap_cell  = (row[1] or "").strip() if len(row) > 1 else ""

        if not date_cell and not cap_cell:
            continue

        # Skip the header row ("FECHA ...") and the totals row ("TOTAL ...").
        if date_cell.upper() == "FECHA":
            continue
        if date_cell.upper().lstrip().startswith("TOTAL"):
            continue

        # Try to recover a real (date, capital) pair.
        try:
            date    = normalize_date(date_cell)
            cap_raw = cap_cell.replace("$", "").replace(" ", "")
            value   = normalize_number(cap_raw)
            data.append((date, value))
            continue
        except ValueError:
            pass

        # Unrecoverable row (e.g. "ERROR DE FECHA" / missing capital):
        # preserve the slot so the user can tell where it was.
        data.append(("0/0", 0.0))

    return sort_by_month(data)




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

    rows = []
    errors = {}
    total_capital = 0.0
    total_interes = 0.0
    total_final   = 0.0

    for idx, (date, capital) in enumerate(input_rows):
        mm, yy = date.split("/")
        year   = "20" + yy
        month  = MONTH_MAP.get(mm)
        if month not in data or year not in data[month]:
            errors[idx] = "ERROR DE FECHA"
            rows.append([date, "ERROR DE FECHA", "", "", "", ""])
            continue
        coeficiente   = data[month][year]
        coef_con_mult = ((coeficiente - 1) * global_mult) + 1
        final   = capital * coef_con_mult
        interes = final - capital
        total_capital += capital
        total_interes += interes
        total_final   += final
        rows.append([
            date,
            format_money(capital),
            f"{coeficiente:.3f}",
            f"{coef_con_mult:.3f}",
            format_money(interes),
            format_money(final),
        ])

    report = {
        "title":   f"Tabla: {tabla_name}",
        "meta":    [f"Fecha de calculo: {calc_date}"],
        "headers": ["FECHA", "CAPITAL", "COEF", f"MULT\n[{global_mult:.2f}]",
                    "INTERES", "CAPITAL + INT"],
        "rows":    rows,
        "totals":  ["TOTAL", format_money(total_capital), "", "",
                    format_money(total_interes), format_money(total_final)],
        "align":   ["l", "r", "r", "r", "r", "r"],
        "errors":  errors,
    }
    return write_output(report, input_rows, output_name)


# ============================
# MODO DESDE PORCENTAJE
# ============================
def from_percent(input_rows, base_percent, ref_date, output_name):
    rows = []
    total_importe = 0.0
    total_interes = 0.0
    total_final   = 0.0

    for date, capital in input_rows:
        diff    = months_diff(date, ref_date)
        percent = diff * base_percent
        interes = capital * (percent / 100)
        final   = capital + interes
        total_importe += capital
        total_interes += interes
        total_final   += final
        rows.append([
            date,
            format_money(capital),
            f"{percent:.2f}",
            format_money(interes),
            format_money(final),
        ])

    report = {
        "title":   "Calculo por porcentaje",
        "meta":    [f"Base: {base_percent:.2f}%",
                    f"Fecha de referencia: {ref_date.strftime('%d/%m/%Y')}"],
        "headers": ["FECHA", "CAPITAL", "%", "INTERES", "CAPITAL + INT"],
        "rows":    rows,
        "totals":  ["TOTAL", format_money(total_importe), "",
                    format_money(total_interes), format_money(total_final)],
        "align":   ["l", "r", "r", "r", "r"],
        "errors":  {},
    }
    return write_output(report, input_rows, output_name)


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
