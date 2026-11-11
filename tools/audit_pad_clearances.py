import re
import math

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

print(f"Total pads extracted: {len(pads)}")

# Check every pair of pads
violations = []
for i in range(len(pads)):
    for j in range(i + 1, len(pads)):
        p1 = pads[i]
        p2 = pads[j]
        
        # Check layer overlap
        p1_thru = (p1['type'] == 'thru_hole') or ('*.Cu' in p1['layers'])
        p2_thru = (p2['type'] == 'thru_hole') or ('*.Cu' in p2['layers'])
        
        layer_overlap = False
        if p1_thru or p2_thru:
            layer_overlap = True
        elif ('F.Cu' in p1['layers'] and 'F.Cu' in p2['layers']) or ('B.Cu' in p1['layers'] and 'B.Cu' in p2['layers']):
            layer_overlap = True
            
        if not layer_overlap:
            continue
            
        # Same net? If same net and not same footprint, distance can be 0 only if connected. But usually different pads.
        if p1['net'] == p2['net'] and p1['net'] > 0 and p1['ref'] != p2['ref']:
            pass # same net
        
        dx = p1['x'] - p2['x']
        dy = p1['y'] - p2['y']
        dist = math.hypot(dx, dy)
        
        r1 = min(p1['sx'], p1['sy']) / 2.0
        r2 = min(p2['sx'], p2['sy']) / 2.0
        
        gap = dist - (r1 + r2)
        
        # JLC minimum clearance: 6 mil = 0.1524 mm
        # If different net, or if same footprint with different net
        if p1['net'] != p2['net']:
            if gap < 0.1524:
                violations.append((p1, p2, gap))

print(f"Clearance violations found: {len(violations)}")
for p1, p2, gap in violations:
    same_fp = " (SAME COMPONENT)" if p1['ref'] == p2['ref'] else ""
    gap_mil = gap / 0.0254
    print(f"  VIOLATION: {p1['ref']}.{p1['num']} (Net {p1['net']} {p1['netname']}) <-> {p2['ref']}.{p2['num']} (Net {p2['net']} {p2['netname']}){same_fp}: gap = {gap:.3f} mm ({gap_mil:.1f} mil)")
