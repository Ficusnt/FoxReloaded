import pathlib

# Constants/Styles
FONT_NORMAL  = ("Segoe UI", 12)
FONT_BOLD    = ("Segoe UI", 12, "bold")
FONT_SMALL   = ("Segoe UI", 10)
BG           = "#f5f5f5"
ACCENT       = "#1565c0"
FG_DARK      = "#212121"
FG_LIGHT     = "#ffffff"

class SavePDFDialog(tk.Toplevel):
    def __init__(self, parent, suggested_name=""):
        super().__init__(parent)
        self.title("Datos del PDF")
        self.configure(bg=BG)
        self.result = None
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        # Pre-fill logic
        admin, edif, unid = "", "", ""
        if suggested_name:
            # Strip .pdf and split by space
            base = suggested_name.replace(".pdf", "")
            parts = base.split(" ", 2)
            if len(parts) >= 1: admin = parts[0]
            if len(parts) >= 2: edif = parts[1]
            if len(parts) >= 3: unid = parts[2]

        container = tk.Frame(self, bg=BG, padx=20, pady=20)
        container.pack()

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

        btn_frame = tk.Frame(container, bg=BG, pady=(20, 0))
        btn_frame.pack()
        
        # Using simple tk.Button for dialog to avoid dependency on _styled_btn outside module
        btn = tk.Button(btn_frame, text="Generar PDF", command=self._on_ok, 
                        bg=ACCENT, fg=FG_LIGHT, font=FONT_BOLD, 
                        relief="flat", padx=20, pady=5, cursor="hand2")
        btn.pack()
        
        # Center
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _on_ok(self):
        self.result = [v.get().strip() for v in self.vars]
        self.destroy()

# Since we are editing a file and not writing a full script, 
# I will prepare these as string blocks for the actual file edit.