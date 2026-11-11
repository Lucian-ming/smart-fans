import re
import sys

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

footprints = text.split('(footprint ')
items = []
for b in footprints[1:]:
    ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', b)
    if not ref_m:
        continue
    ref = ref_m.group(1)
    val_m = re.search(r'\(fp_text\s+value\s+"([^"]+)"', b)
    val = val_m.group(1) if val_m else ''
    fp_name = b.split('\n')[0].strip().strip('"')
    
    # get connected nets
    pads = re.findall(r'\(net\s+\d+\s+"([^"]+)"\)', b)
    unique_nets = sorted(list(set(pads)))
    items.append((ref, val, fp_name, unique_nets))

print(f"Total PCB Footprints: {len(items)}\n")
for ref, val, fp, nets in sorted(items, key=lambda x: x[0]):
    print(f"Ref: {ref:12s} | Val: {val:15s} | FP: {fp:50s} | Nets: {nets}")
