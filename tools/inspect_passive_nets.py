import re

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

footprints = text.split('(footprint ')
refs = []
for b in footprints[1:]:
    ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', b)
    if ref_m:
        refs.append(ref_m.group(1))

print("All components on PCB:", sorted(refs))
print("\nCapacitors:", [r for r in refs if r.startswith('C')])
print("Resistors:", [r for r in refs if r.startswith('R')])
print("Diodes/LEDs:", [r for r in refs if r.startswith('D')])
