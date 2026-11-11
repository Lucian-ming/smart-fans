with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

import re

lines = text.split('\n')
current_fp = None
fps = []

for line in lines:
    if line.strip().startswith('(footprint '):
        current_fp = {'text': line, 'lines': []}
        fps.append(current_fp)
    elif current_fp is not None:
        current_fp['lines'].append(line)
        if line.strip() == ')':
            current_fp = None

print("Parsed footprints:", len(fps))
for fp in fps:
    full = "\n".join(fp['lines'])
    ref_m = re.search(r'\(fp_text\s+reference\s+\"([^\"]+)\"', full)
    val_m = re.search(r'\(fp_text\s+value\s+\"([^\"]+)\"', full)
    at_m = re.search(r'\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', fp['text'] + "\n" + full)
    ref = ref_m.group(1) if ref_m else "?"
    val = val_m.group(1) if val_m else ""
    x = at_m.group(1) if at_m else "?"
    y = at_m.group(2) if at_m else "?"
    
    pads = re.findall(r'\(pad\s+\"([^\"]+)\"[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"', full)
    pads_str = ", ".join([f"{p[0]}:{p[2]}" for p in pads])
    print(f"{ref:12} ({val:10}) at ({x}, {y}) -> {pads_str}")
