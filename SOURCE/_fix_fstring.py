import pathlib
p = pathlib.Path(r'D:\Tools\WebDev\Omniroute\FOX\SOURCE\gui.py')
t = p.read_text('utf-8')

# Fix the broken f-string on line 550
lines = t.splitlines()
for i in range(len(lines)):
    if 'messagebox.showinfo("Listo", f"PDF generado:' in lines[i] and lines[i].endswith(':'):
        # Found the broken line
        if i+1 < len(lines) and '{os.path.basename(res_file)}", parent=self)' in lines[i+1]:
            # Replace the two lines with the correct one
            lines[i] = '        messagebox.showinfo("Listo", f"PDF generado:\\n{os.path.basename(res_file)}", parent=self)'
            lines[i+1] = ''
        break

# Now remove the leftover residue after _generate_done()
for i in range(len(lines)):
    if 'self.master._generate_done()' in lines[i]:
        j = i + 1
        while j < len(lines):
            line = lines[j].strip()
            # Stop at next function definition or empty line that might indicate end of method
            if line.startswith('def ') or (line == '' and j+1 < len(lines) and lines[j+1].strip().startswith('def ')):
                break
            lines[j] = ''
            j += 1
        break

# Join lines and clean up extra blank lines
new_t = '\n'.join(lines)
while new_t.endswith('\n\n'):
    new_t = new_t[:-2]

p.write_text(new_t, 'utf-8')
print('Fixed f-string and cleaned residue')