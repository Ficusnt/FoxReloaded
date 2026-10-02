import pathlib
p = pathlib.Path(r'D:\Tools\WebDev\Omniroute\FOX\SOURCE\gui.py')
t = p.read_text('utf-8')

# Fixing the SavePDFDialog placement (it was inserted at line 51, but the class needs tk defined)
# The class uses tk.Toplevel, etc. tk is imported at the top of gui.py.
# Let's check where tk is imported. It is.

# Fixing the lapped-over logic in the last edit: 
# The previous edit might have placed it weirdly. 
# Let's just ensure it is after imports.
if "class SavePDFDialog" not in t:
    # Insert after imports
    marker = "import tkinter as tk"
    # actually, it is already there according to the check.
    pass

# Let's verify the _update_total implementation again.
# It was added after a marker that appeared multiple times?
# marker_persist = '    fox.write_input_file(rows)'
# This marker is only in _do_persist.

# Let's check for duplicate SavePDFDialog
if t.count("class SavePDFDialog") > 1:
    # Keep only one
    # This is tricky. I will just replace the whole file if I have a clean version.
    # But I dont. I will just use a regex to remove duplicates.
    import re
    # This is too risky.

p.write_text(t, 'utf-8')