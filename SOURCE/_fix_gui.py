import pathlib
p = pathlib.Path(r"D:\Tools\WebDev\Omniroute\FOX\SOURCE\gui.py")
t = p.read_text("utf-8")

# Fix the broken f-string on lines 550-551
# Replace the two lines with a single correct line
lines = t.split("\n")
for i in range(len(lines)):
    if "messagebox.showinfo(\"Listo\", f\"PDF generado:\"" in lines[i] and lines[i].endswith(":"):
        if i+1 < len(lines) and "{os.path.basename(res_file)}\", parent=self)" in lines[i+1]:
            lines[i] = "        messagebox.showinfo(\"Listo\", f\"PDF generado:\\\\n{os.path.basename(res_file)}\", parent=self)"
            lines[i+1] = ""  # Clear the next line
        break

# Remove the leftover residue after _generate_done()
# Find where _generate_done() is and remove everything until the next function definition
for i in range(len(lines)):
    if "self.master._generate_done()" in lines[i]:
        # Remove everything from i+1 until we hit a line that starts with "def " or is a class definition
        j = i + 1
        while j < len(lines):
            line_stripped = lines[j].lstrip()
            if line_stripped.startswith("def ") or line_stripped.startswith("class ") or (line_stripped == "" and j+1 < len(lines) and lines[j+1].lstrip().startswith("def ")):
                break
            lines[j] = ""  # Clear the line
            j += 1
        break

# Join the lines back together
new_t = "\n".join(lines)
# Clean up any extra blank lines at the end
while new_t.endswith("\n\n"):
    new_t = new_t[:-2]

p.write_text(new_t, "utf-8")
print("Fixed gui.py")