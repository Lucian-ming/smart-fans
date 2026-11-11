import re

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

footprints = text.split('(footprint ')
for b in footprints[1:]:
    ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', b)
    if not ref_m:
        continue
    ref = ref_m.group(1)
    if 'VOICE' in ref:
        print(f"=== Ref: {ref} ===")
        pads = re.findall(r'\(pad\s+"([^"]+)"[^\)]*\(at\s+([^\)]+)\)[^\)]*\(net\s+(\d+)\s+"([^"]+)"\)', b)
        for p in pads:
            print(f"  Pad {p[0]}: at ({p[1]}) -> Net: {p[3]}")
