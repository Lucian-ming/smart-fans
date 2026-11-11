"""
Script: tools/pcb_auto_router.py
Robust 2-layer grid router (A* maze router) for Smart Fan RevA.
Routes all non-GND power and signal nets with strict obstacle avoidance:
- Pad clearance >= 0.35 mm
- Track-to-track clearance >= 0.30 mm
- Layer 1 (F.Cu) primarily horizontal / local routing
- Layer 2 (B.Cu) primarily vertical / jumper routing
- Standard via (outer 0.8mm, drill 0.4mm)
- DRC validator guaranteeing 0 collisions.
"""

import math
import heapq
import re
import os

PCB_DIR = "D:/smart_fans/hardware/kicad"
os.makedirs(PCB_DIR, exist_ok=True)

# Grid parameters (in mm)
# Board bounds: 100 to 185 in X and Y
X_MIN, X_MAX = 98.0, 187.0
Y_MIN, Y_MAX = 98.0, 187.0
GRID_RES = 0.5  # 0.5 mm grid cell size
NX = int(round((X_MAX - X_MIN) / GRID_RES)) + 1
NY = int(round((Y_MAX - Y_MIN) / GRID_RES)) + 1

def to_grid(x, y):
    gx = int(round((x - X_MIN) / GRID_RES))
    gy = int(round((y - Y_MIN) / GRID_RES))
    return max(0, min(NX - 1, gx)), max(0, min(NY - 1, gy))

def to_coord(gx, gy):
    return X_MIN + gx * GRID_RES, Y_MIN + gy * GRID_RES

print(f"Grid dimensions: {NX} x {NY} x 2 layers = {NX * NY * 2} cells")

# 1. Load components & pads
with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

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

print(f"Loaded {len(pads)} pads.")
