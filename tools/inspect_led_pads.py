import re

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

footprints = text.split('(footprint ')
for b in footprints[1:]:
    ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', b)
    if not ref_m:
        continue
    ref = ref_m.group(1)
    if ref in ['D4', 'D5', 'Q1', 'Q2']:
        pads = re.findall(r'\(pad\s+"([^"]+)"\s+\w+\s+\w+\s+\(at\s+([^\)]+)\).*?\(net\s+(\d+)\s+"([^"]+)"\)', b)
        print(f"Ref: {ref}")
        for p in pads:
            print(f"  Pad {p[0]}: net={p[3]} at {p[1]}")
