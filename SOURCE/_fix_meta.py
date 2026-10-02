import pathlib
p = pathlib.Path(r'D:\Tools\WebDev\Omniroute\FOX\SOURCE\fox.py')
t = p.read_text('utf-8')

# Fixing from_percent meta block carefully
# It was:
#         "meta":    [f"Base: {base_percent:.2f}%,
#                     f"Fecha de referencia: {ref_date.strftime('%d/%m/%Y')}"],

old_meta_pct = '        "meta":    [f"Base: {base_percent:.2f}%,\n                    f"Fecha de referencia: {ref_date.strftime(\'%d/%m/%Y\')}"]'
# Note: the escaping of % and quotes in PowerShell is a pain. 
# I will use a different marker.
t = t.replace('        "meta":    [f"Base: {base_percent:.2f}%,', '        "meta":    [f"Administracion: {admin}", f"Edificio/Calle: {edif}", f"Unidad: {unid}", f"Base: {base_percent:.2f}%,')

p.write_text(t, 'utf-8')
print('fox.py meta fixed')