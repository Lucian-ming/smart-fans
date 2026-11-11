import re

with open('tools/export_kicad_project.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Move D2 from (126 104) to (130 104)
code = code.replace(
    '(at 126 104)',
    '(at 130 104)'
)

# 2. Fix Q1 TO-92 pad sizes: change from size 1.3 1.3 to size 1.0 1.4 (drill 0.65)
old_q1 = """		(pad "1" thru_hole rect (at -1.27 0) (size 1.3 1.3) (drill 0.8) (layers "*.Cu" "*.Mask") (net 18 "BUZZER_CTRL"))
		(pad "2" thru_hole circle (at 0 0) (size 1.3 1.3) (drill 0.8) (layers "*.Cu" "*.Mask") (net 1 "GND"))
		(pad "3" thru_hole circle (at 1.27 0) (size 1.3 1.3) (drill 0.8) (layers "*.Cu" "*.Mask") (net 24 "BUZ_DRV"))"""

new_q1 = """		(pad "1" thru_hole rect (at -1.27 0) (size 1.0 1.4) (drill 0.65) (layers "*.Cu" "*.Mask") (net 18 "BUZZER_CTRL"))
		(pad "2" thru_hole oval (at 0 0) (size 1.0 1.4) (drill 0.65) (layers "*.Cu" "*.Mask") (net 1 "GND"))
		(pad "3" thru_hole oval (at 1.27 0) (size 1.0 1.4) (drill 0.65) (layers "*.Cu" "*.Mask") (net 24 "BUZ_DRV"))"""

assert old_q1 in code, "old_q1 not found in code!"
code = code.replace(old_q1, new_q1)

# 3. Move SENS1 from (106 163) to (105 156)
old_sens1 = """	(footprint "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
		(layer "F.Cu") (uuid "c1000000-0001-0000-0000-000000000019") (at 106 163)"""
new_sens1 = """	(footprint "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
		(layer "F.Cu") (uuid "c1000000-0001-0000-0000-000000000019") (at 105 156)"""

assert old_sens1 in code, "old_sens1 not found in code!"
code = code.replace(old_sens1, new_sens1)

with open('tools/export_kicad_project.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated tools/export_kicad_project.py successfully!")
