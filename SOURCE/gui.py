"""
gui.py — Interfaz gráfica completa para FOX.

Flujo:
  MainWindow → DataEditor → TablaOptions  → PDF → done dialog
                           → PercentOptions → PDF → done dialog
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime

# ── Fuentes y colores ────────────────────────────────────────────────────────
FONT_NORMAL  = ("Segoe UI", 12)
FONT_BOLD    = ("Segoe UI", 12, "bold")
FONT_TITLE   = ("Segoe UI", 15, "bold")
FONT_SMALL   = ("Segoe UI", 10)
FONT_BTN     = ("Segoe UI", 12)
FONT_ENTRY   = ("Segoe UI", 12)

BG           = "#f5f5f5"
BG_TABLE     = "#ffffff"
ACCENT       = "#1565c0"
ACCENT_DARK  = "#0d47a1"
BTN_DANGER   = "#c62828"
BTN_NEUTRAL  = "#546e7a"
FG_LIGHT     = "#ffffff"
FG_DARK      = "#212121"
ROW_ALT      = "#e8eaf6"
BORDER       = "#bdbdbd"
ERROR_BG     = "#ffebee"
ERROR_FG     = "#b71c1c"


def _styled_btn(parent, text, command, color=None, width=18):
    color = color or ACCENT
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=FG_LIGHT, font=FONT_BTN,
        relief="flat", bd=0, padx=12, pady=6,
        cursor="hand2", width=width,
        activebackground=ACCENT_DARK, activeforeground=FG_LIGHT,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_DARK if color == ACCENT else color))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _center(win, w, h):
    win.update_idletasks()
    x = (win.winfo_screenwidth()  - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def _open_pdf(path):
    """Open a PDF with the system default viewer (cross-platform)."""
    import subprocess
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def _fox():
    """Import fox module — adds SOURCE/ to path if needed."""
    src = os.path.dirname(os.path.abspath(__file__))
    if src not in sys.path:
        sys.path.insert(0, src)
    import fox
    return fox


# ===========================================================================
# DATA EDITOR
# ===========================================================================

class DataEditor(tk.Toplevel):
    """Scrollable table for editing (Fecha MM/AA, Capital) rows.

    Per-row buttons: X delete, pen focus-fecha, + insert below.
    Bottom bar: Limpiar tabla | Cargar desde PDF  //  Cancelar | Continuar ->
    Window auto-sizes to content (capped at 88 % of screen height).
    MouseWheel works from anywhere inside the table area.
    """

    _MAX_H_FRAC = 0.88

    def __init__(self, parent, initial_rows=None):
        super().__init__(parent)
        self.title("Datos a calcular")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.grab_set()
        self.result   = None
        self._entries = []   # list of dicts, one per row
        self._build_ui()
        for date, value in (initial_rows or []):
            self._add_row(date_val=date, cap_val=f"{value:g}")
        if not self._entries:
            self._add_row()
        self._chrome_h = None
        self._auto_resize()
        self.wait_window()

    def _build_ui(self):
        tk.Label(self, text="Datos a calcular", font=FONT_TITLE,
                 bg=BG, fg=FG_DARK).pack(pady=(16, 2))
        tk.Label(self, text="Fecha: MM/AA   Capital: numero (ej. 15000 o 1.500,50)",
                 font=FONT_SMALL, bg=BG, fg="#666").pack(pady=(0, 8))

        # Header — extra column for the action buttons
        hdr = tk.Frame(self, bg=ACCENT)
        hdr.pack(fill="x", padx=20)
        for txt, w in (("#", 3), ("Fecha", 10), ("Capital", 18), ("", 10)):
            tk.Label(hdr, text=txt, width=w, bg=ACCENT, fg=FG_LIGHT,
                     font=FONT_BOLD, anchor="w").pack(side="left", padx=6, pady=4)

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(0, 4))
        self._canvas = tk.Canvas(outer, bg=BG_TABLE, highlightthickness=1,
                                 highlightbackground=BORDER)
        sb = tk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._rf = tk.Frame(self._canvas, bg=BG_TABLE)
        self._cw = self._canvas.create_window((0, 0), window=self._rf, anchor="nw")
        self._rf.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._cw, width=e.width))
        # Scroll when cursor is over the empty canvas background
        self._canvas.bind("<MouseWheel>", self._on_scroll)

        bb = tk.Frame(self, bg=BG)
        bb.pack(fill="x", padx=20, pady=(4, 16))
        _styled_btn(bb, "Limpiar tabla",    self._clear_all,   BTN_DANGER,  14).pack(side="left", padx=(0, 6))
        _styled_btn(bb, "Cargar desde PDF", self._load_pdf,    BTN_NEUTRAL, 16).pack(side="left")
        # spacer pushes right-side buttons to the far right
        tk.Frame(bb, bg=BG).pack(side="left", fill="x", expand=True)
        _styled_btn(bb, "Cancelar",         self.destroy,      BTN_NEUTRAL, 10).pack(side="left", padx=(0, 6))
        _styled_btn(bb, "Continuar ->",     self._on_continue, ACCENT,      14).pack(side="left")

    # ------------------------------------------------------------------
    # Row management
    # ------------------------------------------------------------------

    def _row_bg(self, idx):
        return BG_TABLE if idx % 2 == 0 else ROW_ALT

    def _add_row(self, date_val="", cap_val="", insert_after=None):
        """Append a new row, or insert it immediately after insert_after index."""
        if insert_after is None:
            idx = len(self._entries)
        else:
            idx = insert_after + 1

        bg  = self._row_bg(idx)
        frm = tk.Frame(self._rf, bg=bg)

        if insert_after is None or idx >= len(self._entries):
            frm.pack(fill="x")
        else:
            frm.pack(fill="x", after=self._entries[insert_after]["frame"])

        num_lbl = tk.Label(frm, text=str(idx + 1), width=3, bg=bg,
                           fg="#999", font=FONT_SMALL, anchor="center")
        num_lbl.pack(side="left", padx=(4, 0), pady=3)

        fv = tk.StringVar(value=date_val)
        cv = tk.StringVar(value=cap_val)

        fe = tk.Entry(frm, textvariable=fv, font=FONT_ENTRY,
                      width=10, relief="solid", bd=1)
        fe.pack(side="left", padx=4, pady=3)

        ce = tk.Entry(frm, textvariable=cv, font=FONT_ENTRY,
                      width=18, relief="solid", bd=1, justify="right")
        ce.pack(side="left", padx=4, pady=3)
        ce.bind("<Tab>",    self._tab_from_capital)
        ce.bind("<Return>", self._enter_from_capital)

        btn_del  = tk.Button(frm, text="X", font=("Segoe UI", 9, "bold"),
                             bg=BTN_DANGER,  fg=FG_LIGHT, relief="flat", bd=0,
                             padx=5, pady=2, cursor="hand2", width=2)
        btn_edit = tk.Button(frm, text="~", font=("Segoe UI", 9),
                             bg=BTN_NEUTRAL, fg=FG_LIGHT, relief="flat", bd=0,
                             padx=5, pady=2, cursor="hand2", width=2)
        btn_add  = tk.Button(frm, text="+", font=("Segoe UI", 9, "bold"),
                             bg=ACCENT,      fg=FG_LIGHT, relief="flat", bd=0,
                             padx=5, pady=2, cursor="hand2", width=2)
        btn_add.pack(side="right",  padx=(0, 4), pady=3)
        btn_edit.pack(side="right", padx=(0, 2), pady=3)
        btn_del.pack(side="right",  padx=(0, 2), pady=3)

        row = {
            "frame":       frm,
            "num_lbl":     num_lbl,
            "fecha_var":   fv,
            "cap_var":     cv,
            "fecha_entry": fe,
            "cap_entry":   ce,
            "btn_del":     btn_del,
            "btn_edit":    btn_edit,
            "btn_add":     btn_add,
        }

        self._entries.insert(idx, row)
        self._wire_row(idx)
        self._bind_scroll_recursive(frm)
        self._renumber()
        self.after(50, lambda: self._canvas.yview_moveto(1.0))
        self.after(60, self._auto_resize)

    def _wire_row(self, idx):
        """Attach button commands for the row at idx."""
        row = self._entries[idx]

        def del_cmd(r=row):
            if len(self._entries) == 1:
                r["fecha_var"].set("")
                r["cap_var"].set("")
                r["fecha_entry"].focus_set()
                return
            r["frame"].destroy()
            self._entries.remove(r)
            self._renumber()
            self._recolor()
            self.after(60, self._auto_resize)

        def edit_cmd(r=row):
            r["fecha_entry"].focus_set()
            r["fecha_entry"].icursor("end")

        def add_cmd(r=row):
            i = self._entries.index(r)
            self._add_row(insert_after=i)

        row["btn_del"].config(command=del_cmd)
        row["btn_edit"].config(command=edit_cmd)
        row["btn_add"].config(command=add_cmd)

    def _renumber(self):
        for i, row in enumerate(self._entries):
            row["num_lbl"].config(text=str(i + 1))

    def _recolor(self):
        for i, row in enumerate(self._entries):
            bg = self._row_bg(i)
            row["frame"].config(bg=bg)
            row["num_lbl"].config(bg=bg)

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    def _on_scroll(self, event):
        if event.delta:
            self._canvas.yview_scroll(-1 * (event.delta // 120), "units")
        elif event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")

    def _bind_scroll_recursive(self, widget):
        """Bind MouseWheel on widget and all its descendants."""
        widget.bind("<MouseWheel>", self._on_scroll)
        widget.bind("<Button-4>",   self._on_scroll)
        widget.bind("<Button-5>",   self._on_scroll)
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    # ------------------------------------------------------------------
    # Auto-resize window to content
    # ------------------------------------------------------------------

    def _auto_resize(self):
        self.update_idletasks()
        content_h = self._rf.winfo_reqheight()
        max_h = int(self.winfo_screenheight() * self._MAX_H_FRAC)
        if self._chrome_h is None:
            self._chrome_h = self.winfo_reqheight() - self._canvas.winfo_reqheight()
        w = self.winfo_reqwidth()
        h = min(self._chrome_h + content_h, max_h)
        _center(self, w, h)

    # ------------------------------------------------------------------
    # Tab / Enter keys on capital field
    # ------------------------------------------------------------------

    def _tab_from_capital(self, event):
        """Tab on last row appends a new row; elsewhere moves focus normally."""
        for i, row in enumerate(self._entries):
            if row["cap_entry"] is event.widget:
                if i == len(self._entries) - 1:
                    self._add_row()
                    self.after(80, lambda: self._entries[-1]["fecha_entry"].focus_set())
                    return "break"
                break

    def _enter_from_capital(self, event):
        """Enter always inserts a new row immediately after the current one."""
        for i, row in enumerate(self._entries):
            if row["cap_entry"] is event.widget:
                self._add_row(insert_after=i)
                self.after(80, lambda: self._entries[i + 1]["fecha_entry"].focus_set())
                return "break"

    # ------------------------------------------------------------------
    # Bottom-bar actions
    # ------------------------------------------------------------------

    def _clear_all(self):
        if not messagebox.askyesno(
                "Limpiar tabla",
                "Eliminar todas las filas?",
                parent=self):
            return
        for row in self._entries:
            row["frame"].destroy()
        self._entries.clear()
        self._canvas.yview_moveto(0.0)
        self._add_row()
        try:
            fox = _fox()
            inp = os.path.join(fox.BASE_PATH, "input.txt")
            if os.path.exists(inp):
                os.remove(inp)
        except Exception:
            pass

    def _load_pdf(self):
        fox = _fox()
        planillas = os.path.join(fox.BASE_PATH, "PLANILLAS")
        os.makedirs(planillas, exist_ok=True)
        pdf_path = filedialog.askopenfilename(
            title="Seleccionar PDF",
            initialdir=planillas,
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos", "*.*")],
            parent=self,
        )
        if not pdf_path:
            return
        try:
            rows = fox.load_input_from_pdf(pdf_path)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el PDF:\n{exc}", parent=self)
            return
        if not rows:
            messagebox.showerror(
                "PDF incompatible",
                "El PDF no contiene datos compatibles con este programa.",
                parent=self)
            return
        for row in self._entries:
            row["frame"].destroy()
        self._entries.clear()
        for date, value in rows:
            self._add_row(date_val=date, cap_val=f"{value:g}")

    # ------------------------------------------------------------------
    # Validation and submit
    # ------------------------------------------------------------------

    def _on_continue(self):
        fox    = _fox()
        rows   = []
        errors = False
        for row in self._entries:
            fd = row["fecha_var"].get().strip()
            cd = row["cap_var"].get().strip()
            if not fd and not cd:
                continue
            ok_f = ok_c = True
            fe = row["fecha_entry"]
            ce = row["cap_entry"]
            try:
                fn = fox.normalize_date(fd)
                fe.config(bg=BG_TABLE)
            except Exception:
                fe.config(bg=ERROR_BG); ok_f = False; errors = True
            try:
                cn = fox.normalize_number(cd)
                ce.config(bg=BG_TABLE)
            except Exception:
                ce.config(bg=ERROR_BG); ok_c = False; errors = True
            if ok_f and ok_c:
                rows.append((fn, cn))
        if errors:
            messagebox.showerror(
                "Error en los datos",
                "Hay celdas en rojo con valores invalidos.\n\n"
                "Fecha: formato MM/AA (ej. 03/24)\n"
                "Capital: numero (ej. 15000 o 1.500,50)",
                parent=self)
            return
        if not rows:
            messagebox.showerror("Sin datos", "Ingrese al menos una fila.", parent=self)
            return
        self.result = fox.sort_by_month(rows)
        self.destroy()


# ===========================================================================
# TABLA OPTIONS
# ===========================================================================

class TablaOptions(tk.Toplevel):
    def __init__(self, parent, input_rows):
        super().__init__(parent)
        self.title("Configuracion de tabla")
        self.configure(bg=BG)
        self.grab_set()
        self._rows = input_rows
        self._csvs = _fox().get_csv_files()
        self._build_ui()
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 480)
        h = self.winfo_reqheight()
        self.resizable(False, False)
        _center(self, w, h)
        self.wait_window()

    def _build_ui(self):
        tk.Label(self, text="Seleccionar tabla (CSV)", font=FONT_TITLE,
                 bg=BG, fg=FG_DARK).pack(pady=(20, 12))

        if not self._csvs:
            tk.Label(self, text="No se encontraron archivos CSV en la carpeta TABLAS.",
                     font=FONT_NORMAL, bg=BG, fg="#b71c1c", wraplength=400).pack(pady=20)
            _styled_btn(self, "Cerrar", self.destroy, BTN_NEUTRAL, 12).pack()
            return

        lf = tk.Frame(self, bg=BG)
        lf.pack(padx=24, fill="x")
        tk.Label(lf, text="Tabla:", font=FONT_BOLD, bg=BG, fg=FG_DARK).pack(anchor="w")

        lbf = tk.Frame(lf, bg=BG)
        lbf.pack(fill="x", pady=(2, 10))
        sb = tk.Scrollbar(lbf, orient="vertical")
        self._lb = tk.Listbox(lbf, font=FONT_ENTRY, height=7,
                              yscrollcommand=sb.set, selectmode="single",
                              relief="solid", bd=1, activestyle="dotbox",
                              selectbackground=ACCENT, selectforeground=FG_LIGHT)
        sb.config(command=self._lb.yview)
        sb.pack(side="right", fill="y")
        self._lb.pack(side="left", fill="x", expand=True)
        for f in self._csvs:
            self._lb.insert("end", f)
        self._lb.selection_set(0)

        mf = tk.Frame(self, bg=BG)
        mf.pack(padx=24, fill="x", pady=(0, 16))
        tk.Label(mf, text="Multiplicador global:", font=FONT_BOLD,
                 bg=BG, fg=FG_DARK).pack(anchor="w")
        self._mv = tk.StringVar(value="1")
        tk.Entry(mf, textvariable=self._mv, font=FONT_ENTRY,
                 width=10, relief="solid", bd=1).pack(anchor="w", pady=(2, 0))

        bb = tk.Frame(self, bg=BG)
        bb.pack(padx=24, fill="x", pady=(0, 20))
        _styled_btn(bb, "Cancelar",    self.destroy,   BTN_NEUTRAL, 10).pack(side="right", padx=(0, 6))
        _styled_btn(bb, "Generar PDF", self._generate, ACCENT,      14).pack(side="right")

    def _generate(self):
        sel = self._lb.curselection()
        if not sel:
            messagebox.showerror("Sin seleccion", "Seleccione un CSV.", parent=self)
            return
        try:
            mult = float(self._mv.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "El multiplicador debe ser un numero.", parent=self)
            return

        name = simpledialog.askstring("Nombre del archivo",
                                      "Nombre del PDF (sin extension):", parent=self)
        if not name or not name.strip():
            return

        try:
            path = _fox().from_tabla(self._rows, self._csvs[sel[0]], mult, name.strip())
        except Exception as exc:
            messagebox.showerror("Error al generar PDF", str(exc), parent=self)
            return

        messagebox.showinfo("Listo", f"PDF generado:\n\n{path}", parent=self)
        _open_pdf(path)
        self.destroy()


# ===========================================================================
# PERCENT OPTIONS
# ===========================================================================

class PercentOptions(tk.Toplevel):
    def __init__(self, parent, input_rows):
        super().__init__(parent)
        self.title("Configuracion de porcentaje")
        self.configure(bg=BG)
        self.grab_set()
        self._rows = input_rows
        self._build_ui()
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 420)
        h = self.winfo_reqheight()
        self.resizable(False, False)
        _center(self, w, h)
        self.wait_window()

    def _build_ui(self):
        tk.Label(self, text="Calculo por porcentaje", font=FONT_TITLE,
                 bg=BG, fg=FG_DARK).pack(pady=(20, 16))
        form = tk.Frame(self, bg=BG)
        form.pack(padx=32, fill="x")

        tk.Label(form, text="Porcentaje base mensual (%):", font=FONT_BOLD,
                 bg=BG, fg=FG_DARK).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._pv = tk.StringVar()
        tk.Entry(form, textvariable=self._pv, font=FONT_ENTRY,
                 width=12, relief="solid", bd=1).grid(row=1, column=0, sticky="w", pady=(0, 16))

        tk.Label(form, text="Desplazar mes:", font=FONT_BOLD,
                 bg=BG, fg=FG_DARK).grid(row=2, column=0, sticky="w", pady=(0, 2))
        tk.Label(form, text="(0 = mes actual, +2 = dos meses adelante, -1 = mes anterior)",
                 font=FONT_SMALL, bg=BG, fg="#777", wraplength=340,
                 justify="left").grid(row=3, column=0, sticky="w", pady=(0, 4))
        self._sv = tk.StringVar(value="0")
        tk.Entry(form, textvariable=self._sv, font=FONT_ENTRY,
                 width=8, relief="solid", bd=1).grid(row=4, column=0, sticky="w")

        bb = tk.Frame(self, bg=BG)
        bb.pack(padx=24, fill="x", pady=(24, 20))
        _styled_btn(bb, "Cancelar",    self.destroy,   BTN_NEUTRAL, 10).pack(side="right", padx=(0, 6))
        _styled_btn(bb, "Generar PDF", self._generate, ACCENT,      14).pack(side="right")

    def _generate(self):
        try:
            pct = float(self._pv.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error",
                                 "Ingrese un porcentaje valido (ej. 5 o 3,5).", parent=self)
            return

        shift_raw = self._sv.get().strip()
        shift = 0
        if shift_raw and shift_raw not in ("0", "+0", "-0"):
            try:
                shift = int(shift_raw)
            except ValueError:
                messagebox.showerror("Error",
                                     "Desplazar mes debe ser un numero entero (ej. 0, 2, -1).",
                                     parent=self)
                return
            if abs(shift) > 120:
                if not messagebox.askyesno(
                        "Desplazamiento inusual",
                        f"El desplazamiento es de {shift} meses ({abs(shift) // 12} años aprox.).\n"
                        "¿Continuar de todas formas?",
                        parent=self):
                    return

        today = datetime.today()
        total_months = (today.year * 12 + today.month - 1) + shift
        ref_year  = total_months // 12
        ref_month = total_months %  12 + 1
        ref_date  = datetime(ref_year, ref_month, 1)

        name = simpledialog.askstring("Nombre del archivo",
                                      "Nombre del PDF (sin extension):", parent=self)
        if not name or not name.strip():
            return

        try:
            path = _fox().from_percent(self._rows, pct, ref_date, name.strip())
        except Exception as exc:
            messagebox.showerror("Error al generar PDF", str(exc), parent=self)
            return

        messagebox.showinfo("Listo", f"PDF generado:\n\n{path}", parent=self)
        _open_pdf(path)
        self.destroy()


# ===========================================================================
# MAIN WINDOW
# ===========================================================================

class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("FOX")
        self.configure(bg=BG)
        self._build_ui()
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 440)
        h = self.winfo_reqheight()
        self.resizable(False, False)
        _center(self, w, h)
        self.protocol("WM_DELETE_WINDOW", self._cleanup_and_exit)

    def _build_ui(self):
        tk.Label(self, text="FOX", font=("Segoe UI", 38, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(36, 2))
        tk.Label(self, text="Actualizador de valores",
                 font=FONT_NORMAL, bg=BG, fg="#555").pack(pady=(0, 36))

        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=40)
        bf.columnconfigure(0, weight=1)
        for i, (label, cmd, color) in enumerate([
            ("Tablas",                      self._open_tablas,     ACCENT),
            ("Porcentaje",                  self._open_porcentaje, ACCENT),
            ("Actualizar tablas (scraper)", self._run_scraper,     BTN_NEUTRAL),
        ]):
            btn = tk.Button(
                bf, text=label, command=cmd,
                bg=color, fg=FG_LIGHT, font=FONT_BTN,
                relief="flat", bd=0, padx=12, pady=6,
                cursor="hand2",
                activebackground=ACCENT_DARK, activeforeground=FG_LIGHT,
            )
            btn.grid(row=i, column=0, sticky="ew", pady=7)
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=ACCENT_DARK if c == ACCENT else c))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

        tk.Label(self, text="", bg=BG).pack(expand=True)
        tk.Label(self, text="v2.0", font=FONT_SMALL, bg=BG, fg="#ccc").pack(pady=(0, 10))

    def _edit_rows(self):
        """Open DataEditor pre-populated from input.txt. Returns result list or None."""
        fox = _fox()
        initial = fox.read_input_file() or []
        ed = DataEditor(self, initial)
        if ed.result is None:
            return None
        inp = os.path.join(fox.BASE_PATH, "input.txt")
        with open(inp, "w", encoding="utf-8") as f:
            for date, value in ed.result:
                f.write(f"{date} {value:.2f}\n")
        return ed.result

    def _open_tablas(self):
        rows = self._edit_rows()
        if rows is not None:
            TablaOptions(self, rows)

    def _open_porcentaje(self):
        rows = self._edit_rows()
        if rows is not None:
            PercentOptions(self, rows)

    def _cleanup_and_exit(self):
        try:
            inp = os.path.join(_fox().BASE_PATH, "input.txt")
            if os.path.exists(inp):
                os.remove(inp)
        except Exception:
            pass
        self.destroy()

    def _run_scraper(self):
        win = tk.Toplevel(self)
        win.title("Actualizando tablas...")
        win.configure(bg=BG)
        win.grab_set()
        tk.Label(win, text="Conectando con el servidor...",
                 font=FONT_NORMAL, bg=BG, fg=FG_DARK, wraplength=360).pack(pady=(40, 16))
        bar = ttk.Progressbar(win, mode="indeterminate", length=300)
        bar.pack(padx=50)
        bar.start(12)
        win.update_idletasks()
        w = max(win.winfo_reqwidth(), 400)
        h = win.winfo_reqheight()
        win.resizable(False, False)
        _center(win, w, h)

        def run():
            try:
                import scraper
                scraper.run_scrape()
                win.after(0, lambda: _done(True, None))
            except Exception as exc:
                win.after(0, lambda e=exc: _done(False, e))

        def _done(ok, exc):
            bar.stop()
            win.destroy()
            if ok:
                messagebox.showinfo("Listo", "Tablas actualizadas correctamente.", parent=self)
            else:
                messagebox.showerror("Error",
                                     f"No se pudieron actualizar las tablas:\n{exc}", parent=self)

        threading.Thread(target=run, daemon=True).start()


# ===========================================================================
# ENTRY POINT
# ===========================================================================

def run_app():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run_app()

