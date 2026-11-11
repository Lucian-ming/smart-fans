import re

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

footprints = text.split('(footprint ')
for b in footprints[1:]:
    ref_m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', b)
    if not ref_m:
        continue
    ref = ref_m.group(1)
    if 'MCU' in ref or 'VOICE' in ref or 'OLED' in ref or 'GESTURE' in ref or 'SERVO' in ref:
        lines = b.split('\n')
        fp_name = lines[0].strip().strip('"')
        at_m = re.search(r'\(at\s+([^\)]+)\)', b[:300])
        at_str = at_m.group(1) if at_m else '?'
        
        # pads
        pad_matches = re.findall(r'\(pad\s+"([^"]+)"\s+\w+\s+\w+\s+\(at\s+([^\)]+)\)', b)
        print(f"Ref: {ref}")
        print(f"  Footprint: {fp_name}")
        print(f"  Footprint (at): {at_str}")
        print(f"  First 3 pads: {pad_matches[:3]}")
        if len(pad_matches) > 3:
            print(f"  Last pad: {pad_matches[-1]}")
