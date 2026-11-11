import re

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

footprints = text.split('(footprint ')
print(f"Total footprint blocks: {len(footprints)-1}")
items = []
for b in footprints[1:]:
    lines = b.split('\n')
    fp_name = lines[0].strip().strip('"')
    ref_match = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', b)
    val_match = re.search(r'\(fp_text\s+value\s+"([^"]+)"', b)
    ref = ref_match.group(1) if ref_match else '?'
    val = val_match.group(1) if val_match else '?'
    items.append((ref, val, fp_name))

for ref, val, fp in sorted(items, key=lambda x: x[0]):
    print(f"{ref:12s} | {val:25s} | {fp}")
