with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'\(footprint\s+\"([^\"]+)\"[\s\S]*?\(fp_text\s+reference\s+\"([^\"]+)\"[\s\S]*?\n\t\)', text):
    ref = m.group(2)
    if ref in ['Q1', 'DC1', 'D2', 'BZ1', 'SENS1', 'U2', 'C1', 'C2']:
        print(f"=== {ref} ===")
        print(m.group(0))
