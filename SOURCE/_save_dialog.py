import pathlib
import os
import tkinter as tk

# Constants/Styles
FONT_NORMAL  = ("Segoe UI", 12)
FONT_BOLD    = ("Segoe UI", 12, "bold")
FONT_SMALL   = ("Segoe UI", 10)
BG           = "#f5f5f5"
ACCENT       = "#1565c0"
FG_DARK      = "#212121"
FG_LIGHT     = "#ffffff"

class SavePDFDialog(tk.Frame):
    def __init__(self, parent, suggested_name="", on_ok=None, on_back=None):
        super().__init__(parent, bg=BG)
        self.on_ok = on_ok
        self.on_back = on_back

        # Pre-fill logic
        admin, edif, unid = "", "", ""
        if suggested_name:
            # Ensure we only use the filename, not the full path
            filename = os.path.basename(suggested_name)
            # Strip .pdf and split by space
            base = filename.replace(".pdf", "")
            parts = base.split(" ", 2)
            if len(parts) >= 1: admin = parts[0]
            if len(parts) >= 2: edif = parts[1]
            if len(parts) >= 3: unid = parts[2]

        container = tk.Frame(self, bg=BG, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        fields = [
            ("Administracion:", admin),
            ("Edificio/Calle:", edif),
            ("Unidad:", unid)
        ]

        self.vars = []
        for label_text, default_val in fields:
            row = tk.Frame(container, bg=BG)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label_text, font=FONT_NORMAL, bg=BG, fg=FG_DARK, width=15, anchor="w").pack(side="left")
            var = tk.StringVar(value=default_val)
            tk.Entry(row, textvariable=var, font=FONT_NORMAL, width=25, relief="solid", bd=1).pack(side="left", padx=5)
            self.vars.append(var)

        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack()

        # Using simple tk.Button for dialog to avoid dependency on _styled_btn outside module
        if self.on_back:
            back_btn = tk.Button(btn_frame, text="Volver", command=self._on_back,
                                bg="#757575", fg=FG_LIGHT, font=FONT_NORMAL,
                                relief="flat", padx=20, pady=5, cursor="hand2")
            back_btn.pack(side="left", padx=(0, 10))

        btn = tk.Button(btn_frame, text="Generar PDF", command=self._on_ok,
                        bg=ACCENT, fg=FG_LIGHT, font=FONT_BOLD,
                        relief="flat", padx=20, pady=5, cursor="hand2")
        btn.pack(side="left")

    def _on_ok(self):
        data = [v.get().strip() for v in self.vars]
        if self.on_ok:
            self.on_ok(data)

    def _on_back(self):
        if self.on_back:
            self.destroy()
            self.on_back()
