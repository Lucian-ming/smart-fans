import re
import sys

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

# Match footprints and their references
pattern = re.compile(r'\(footprint\s+"([^"]+)".*?\(property\s+"Reference"\s+"([^"]+)"', re.DOTALL)
matches = pattern.findall(text)
print(f"Total footprints on PCB: {len(matches)}")
for fp, ref in sorted(matches, key=lambda x: x[1]):
    print(f"Ref: {ref:8s} | Footprint: {fp}")
