with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

import re
import math

# Parse footprints
footprint_blocks = re.findall(r'\(footprint\s+.*?\n\t\)', text, re.DOTALL)
print(f"Footprints found: {len(footprint_blocks)}")

# Parse pads with locations
pads = []
for block in footprint_blocks:
    ref_m = re.search(r'\(fp_text\s+reference\s+\"([^\"]+)\"', block)
    ref = ref_m.group(1) if ref_m else "?"
    at_m = re.search(r'\(footprint\s+\"[^\"]+\"\s+.*?\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', block)
    if not at_m:
        continue
    fx = float(at_m.group(1))
    fy = float(at_m.group(2))
    frot = float(at_m.group(3)) if at_m.group(3) else 0.0

    # find all pads in this block
    # each pad line: (pad "num" type shape (at x y [rot]) (size sx sy) ... (layers ...) [(net id "name")])
    for pm in re.finditer(r'\(pad\s+\"([^\"]+)\"\s+(\S+)\s+(\S+)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)\s+\(size\s+([\d\.\-]+)\s+([\d\.\-]+)\)[\s\S]*?\(layers\s+([^\)]+)\)(?:[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"\))?', block):
        pnum = pm.group(1)
        ptype = pm.group(2)
        pshape = pm.group(3)
        lx = float(pm.group(4))
        ly = float(pm.group(5))
        prot = float(pm.group(6)) if pm.group(6) else 0.0
        sx = float(pm.group(7))
        sy = float(pm.group(8))
        layers = pm.group(9)
        nid = int(pm.group(10)) if pm.group(10) else 0
        nname = pm.group(11) if pm.group(11) else ""

        # calc abs position
        rad = math.radians(frot)
        ax = fx + (lx * math.cos(rad) - ly * math.sin(rad))
        ay = fy + (lx * math.sin(rad) + ly * math.cos(rad))
        pads.append({
            'ref': ref, 'num': pnum, 'type': ptype, 'shape': pshape,
            'x': ax, 'y': ay, 'sx': sx, 'sy': sy, 'layers': layers,
            'net': nid, 'netname': nname
        })

print(f"Total pads extracted: {len(pads)}")

# Parse segments
segments = []
for sm in re.finditer(r'\(segment\s+\(start\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(end\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(width\s+([\d\.\-]+)\)\s+\(layer\s+\"([^\"]+)\"\)\s+\(net\s+(\d+)\)\)', text):
    x1, y1 = float(sm.group(1)), float(sm.group(2))
    x2, y2 = float(sm.group(3)), float(sm.group(4))
    w = float(sm.group(5))
    layer = sm.group(6)
    nid = int(sm.group(7))
    segments.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'w': w, 'layer': layer, 'net': nid})

print(f"Total segments extracted: {len(segments)}")

def dist_point_to_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1)*dx + (py - y1)*dy) / l2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

# Check clearance between segments and pads of DIFFERENT nets
clearance_req = 0.25 # mm
short_circuits = []
for s_idx, s in enumerate(segments):
    for p in pads:
        if s['net'] == p['net']:
            continue # same net
        # check layer compatibility
        # If pad is thru_hole, it is on *.Cu (both F.Cu and B.Cu)
        # If pad is smd, check layer
        pad_is_thru = (p['type'] == 'thru_hole') or ('*.Cu' in p['layers'])
        seg_layer = s['layer']
        if not pad_is_thru and seg_layer not in p['layers']:
            continue
        
        d = dist_point_to_segment(p['x'], p['y'], s['x1'], s['y1'], s['x2'], s['y2'])
        pad_radius = min(p['sx'], p['sy']) / 2.0
        seg_radius = s['w'] / 2.0
        gap = d - (pad_radius + seg_radius)
        if gap < clearance_req:
            short_circuits.append({
                'seg_idx': s_idx,
                'seg_net': s['net'],
                'layer': s['layer'],
                'pad': f"{p['ref']}.{p['num']}",
                'pad_net': p['net'],
                'gap': gap
            })

print(f"\nClearance / Short circuit conflicts found: {len(short_circuits)}")
for sc in short_circuits[:20]:
    print(f"  Conflict: Seg #{sc['seg_idx']} (Net {sc['seg_net']}, {sc['layer']}) intersects Pad {sc['pad']} (Net {sc['pad_net']}) with gap {sc['gap']:.3f} mm")
