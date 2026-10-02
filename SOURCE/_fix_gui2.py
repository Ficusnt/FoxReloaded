import pathlib
p = pathlib.Path(r"D:\Tools\WebDev\Omniroute\FOX\SOURCE\gui.py")
t = p.read_text("utf-8")

# Fix the broken f-string
lines = t.split("\n")
for i in range(len(lines)):
    if "messagebox.showinfo(\"Listo\", f\"PDF generado:\"" in lines[i] and lines[i].endswith(":"):
        if i+1 < len(lines) and "{os.path.basename(res_file)}\", parent=self)" in lines[i+1]:
            lines[i] = "        messagebox.showinfo(\"Listo\", f\"PDF generado:\\\\n{os.path.basename(res_file)}\", parent=self)"
            lines[i+1] = ""  # Clear the next line
        break

# Remove leftover after _generate_done()
for i in range(len(lines)):
    if "self.master._generate_done()" in lines[i]:
        j = i + 1
        while j < len(lines):
            line_stripped = lines[j].lstrip()
            if line_stripped.startswith("def ") or line_stripped.startswith("class ") or (line_stripped == "" and j+1 < len(lines) and lines[j+1].lstrip().startswith("def ")):
                break
            lines[j] = ""
            j += 1
        break

new_t = "\n".join(lines)
while new_t.endswith("\n\n"):
    new_t = new_t[:-2]

p.write_text(new_t, "utf-8")
print("Fixed f-string and cleaned residue")