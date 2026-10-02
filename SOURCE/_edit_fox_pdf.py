import pathlib
p = pathlib.Path(r'D:\Tools\WebDev\Omniroute\FOX\SOURCE\fox.py')
t = p.read_text('utf-8')

# 1. Update from_tabla signature and call write_output
old_tabla = 'def from_tabla(input_rows, csv_rel_path, global_mult, output_name):'
new_tabla = 'def from_tabla(input_rows, csv_rel_path, global_mult, output_name, admin="", edif="", unid=""):'
t = t.replace(old_tabla, new_tabla)

# Update the report dict in from_tabla to include admin/edif/unid in meta
marker = '        "meta":    [f"Fecha de calculo: {calc_date}"],'
new_meta = f'''        "meta":    [
            f"Administracion: {{admin}}",
            f"Edificio/Calle: {{edif}}",
            f"Unidad: {{unid}}",
            f"Fecha de calculo: {{calc_date}}"
        ],'''
# This is a bit tricky because of the f-string. Let's use a safer replacement.
# I will replace the meta line and the next few.
t = t.replace(marker, '        "meta":    [f"Administracion: {admin}", f"Edificio/Calle: {edif}", f"Unidad: {unid}", f"Fecha de calculo: {calc_date}"],')

# 2. Update from_percent signature
old_pct = 'def from_percent(input_rows, base_percent, ref_date, output_name):'
new_pct = 'def from_percent(input_rows, base_percent, ref_date, output_name, admin="", edif="", unid=""):'
t = t.replace(old_pct, new_pct)

# Update the report dict in from_percent
marker_pct = '        "meta":    [f"Base: {base_percent:.2f}%,'
new_meta_pct = '        "meta":    [f"Administracion: {admin}", f"Edificio/Calle: {edif}", f"Unidad: {unid}", f"Base: {base_percent:.2f}%,'
t = t.replace(marker_pct, new_meta_pct)

p.write_text(t, 'utf-8')
print('fox.py updated')