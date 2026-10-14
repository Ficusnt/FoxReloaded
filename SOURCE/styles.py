import tkinter as tk

# Colors
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

# Fonts
FONT_NORMAL  = ("Segoe UI", 12)
FONT_BOLD    = ("Segoe UI", 12, "bold")
FONT_TITLE   = ("Segoe UI", 15, "bold")
FONT_SMALL   = ("Segoe UI", 10)

def _styled_btn(parent, text, command, color=None, width=18):
    color = color or ACCENT
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=FG_LIGHT, font=FONT_NORMAL,
        relief="flat", bd=0, padx=12, pady=6,
        cursor="hand2", width=width,
        activebackground=ACCENT_DARK, activeforeground=FG_LIGHT,
    )
    return btn

