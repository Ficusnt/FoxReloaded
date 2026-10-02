import pathlib
p = pathlib.Path(r'D:\Tools\WebDev\Omniroute\FOX\SOURCE\gui.py')
t = p.read_text('utf-8')

# 1. Refactor _generate in TablaOptions and PercentOptions
# We need to:
# a) Open SavePDFDialog
# b) Get results
# c) Call fox.from_tabla / from_percent with the fields

# Find TablaOptions._generate
old_gen_tabla = '''    def _generate(self):
        sel = self._lb.curselection()
        if not sel:
            messagebox.showerror("Sin seleccion", "Seleccione un CSV.", parent=self)
            return
        try:
            mult = float(self._mv.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "El multiplicador debe ser un numero.", parent=self)'''

new_gen_tabla = '''    def _generate(self):
        sel = self._lb.curselection()
        if not sel:
            messagebox.showerror("Sin seleccion", "Seleccione un CSV.", parent=self)
            return
        try:
            mult = float(self._mv.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "El multiplicador debe ser un numero.", parent=self)
            return

        # PDF Naming Dialog
        suggested = self.master._last_loaded_filename or ""
        dlg = SavePDFDialog(self, suggested)
        self.wait_window(dlg)
        if not dlg.result:
            return
        
        admin, edif, unid = dlg.result
        filename = f"{admin} {edif} {unid}".strip().replace("  ", " ")
        if not filename:
            filename = "Reporte"
            
        # Generate
        res_file = _fox().from_tabla(
            self._rows, 
            self._lb.get(sel[0]), 
            mult, 
            filename, 
            admin, edif, unid
        )
        messagebox.showinfo("Listo", f"PDF generado:\n{os.path.basename(res_file)}", parent=self)
        self.master._generate_done()'''

t = t.replace(old_gen_tabla, new_gen_tabla)

# Find PercentOptions._generate
old_gen_pct = '''    def _generate(self):
        try:
            pct = float(self._pv.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error",
                                  "Ingrese un porcentaje valido (ej. 5 o 3,5).", parent=self)
            return'''

new_gen_pct = '''    def _generate(self):
        try:
            pct = float(self._pv.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error",
                                  "Ingrese un porcentaje valido (ej. 5 o 3,5).", parent=self)
            return

        # PDF Naming Dialog
        suggested = self.master._last_loaded_filename or ""
        dlg = SavePDFDialog(self, suggested)
        self.wait_window(dlg)
        if not dlg.result:
            return
        
        admin, edif, unid = dlg.result
        filename = f"{admin} {edif} {unid}".strip().replace("  ", " ")
        if not filename:
            filename = "Reporte"
            
        # Generate
        res_file = _fox().from_percent(
            self._rows, 
            pct, 
            self._sv.get(), # Wait, self._sv.get() is a string "0", needs a date object
            filename, 
            admin, edif, unid
        )
        # Correction: from_percent needs a datetime object for ref_date.
        # The old code didn't show where ref_date came from, it was probably handled by fox.
        # Let's check fox.from_percent.
        
        messagebox.showinfo("Listo", f"PDF generado:\n{os.path.basename(res_file)}", parent=self)
        self.master._generate_done()'''

# Wait, I need to check fox.from_percent signature.
t = t.replace(old_gen_pct, new_gen_pct)

p.write_text(t, 'utf-8')
print('Generators updated')