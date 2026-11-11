import re
import math
import heapq

# 1. Parse all pads from export_kicad_project.py or fan_ctrl_revA.kicad_pcb
with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect all pad coordinates and nets
lines = text.split('\n')
fps = []
curr = None
for line in lines:
    if line.strip().startswith('(footprint '):
        curr = {'header': line, 'lines': []}
        fps.append(curr)
    elif curr is not None:
        curr['lines'].append(line)
        if line.strip() == ')':
            curr = None

pads = []
for fp in fps:
    full = "\n".join(fp['lines'])
    ref_m = re.search(r'\(fp_text\s+reference\s+\"([^\"]+)\"', full)
    ref = ref_m.group(1) if ref_m else "?"
    at_m = re.search(r'\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', fp['header'] + "\n" + full)
    fx = float(at_m.group(1)) if at_m else 0
    fy = float(at_m.group(2)) if at_m else 0
    frot = float(at_m.group(3)) if at_m and at_m.group(3) else 0

    for pm in re.finditer(r'\(pad\s+\"([^\"]+)\"\s+(\S+)\s+(\S+)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)\s+\(size\s+([\d\.\-]+)\s+([\d\.\-]+)\)[\s\S]*?\(layers\s+([^\)]+)\)(?:[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"\))?', full):
        pnum = pm.group(1)
        ptype = pm.group(2)
        pshape = pm.group(3)
        lx = float(pm.group(4))
        ly = float(pm.group(5))
        sx = float(pm.group(7))
        sy = float(pm.group(8))
        layers = pm.group(9)
        nid = int(pm.group(10)) if pm.group(10) else 0
        nname = pm.group(11) if pm.group(11) else ""

        rad = math.radians(frot)
        ax = fx + (lx * math.cos(rad) - ly * math.sin(rad))
        ay = fy + (lx * math.sin(rad) + ly * math.cos(rad))
        pads.append({
            'ref': ref, 'num': pnum, 'type': ptype, 'shape': pshape,
            'x': ax, 'y': ay, 'sx': sx, 'sy': sy, 'layers': layers,
            'net': nid, 'netname': nname
        })

print(f"Loaded {len(pads)} pads from PCB.")
net_map = {}
for p in pads:
    if p['net'] > 0:
        net_map.setdefault(p['net'], []).append(p)

for nid in sorted(net_map.keys()):
    print(f"Net {nid:2d} ({net_map[nid][0]['netname']:12s}): {len(net_map[nid])} pads -> {[p['ref']+'.'+p['num'] for p in net_map[nid]]}")
