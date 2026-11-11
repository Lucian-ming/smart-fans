import re

with open('hardware/kicad/fan_ctrl_revA.kicad_sch', 'r', encoding='utf-8') as f:
    text = f.read()

syms = re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', text)
print(f"Total symbols in schematic: {len(syms)}")
print(sorted(set(syms)))
