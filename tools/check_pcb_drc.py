import re
import math

with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's parse all footprints
fps = re.findall(r'\(footprint\s+\"([^\"]+)\"[\s\S]*?\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)[\s\S]*?\(fp_text\s+reference\s+\"([^\"]+)\"[\s\S]*?\n\t\)', text)
print(f"Total footprints parsed: {len(fps)}")

# Count pads and nets
# In KiCad, each footprint has pads.
# Let's count pads
pads = []
# Find each footprint block
fp_blocks = re.findall(r'\(footprint\s+\"([^\"]+)\"[\s\S]*?\n\t\)', text)
print(f"Footprint blocks: {len(fp_blocks)}")

for block in fp_blocks:
    ref_m = re.search(r'\(fp_text\s+reference\s+\"([^\"]+)\"', block)
    ref = ref_m.group(1) if ref_m else "?"
    at_m = re.search(r'\(footprint\s+\"[^\"]+\"[\s\S]*?\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', block)
    fp_x = float(at_m.group(1)) if at_m else 0
    fp_y = float(at_m.group(2)) if at_m else 0
    fp_rot = float(at_m.group(3)) if at_m and at_m.group(3) else 0
    
    # find pads
    pad_matches = re.finditer(r'\(pad\s+\"([^\"]+)\"\s+(\S+)\s+(\S+)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)[\s\S]*?\(layers\s+([^\)]+)\)(?:[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"\))?', block)
    for pm in pad_matches:
        p_num = pm.group(1)
        p_type = pm.group(2)
        p_shape = pm.group(3)
        p_lx = float(pm.group(4))
        p_ly = float(pm.group(5))
        p_rot = float(pm.group(6)) if pm.group(6) else 0
        p_layers = pm.group(7)
        p_net = int(pm.group(8)) if pm.group(8) else 0
        p_netname = pm.group(9) if pm.group(9) else ""
        
        # calculate abs x, y
        rad = math.radians(fp_rot)
        abs_x = fp_x + (p_lx * math.cos(rad) - p_ly * math.sin(rad))
        abs_y = fp_y + (p_lx * math.sin(rad) + p_ly * math.cos(rad))
        
        pads.append({
            'ref': ref,
            'num': p_num,
            'type': p_type,
            'shape': p_shape,
            'x': abs_x,
            'y': abs_y,
            'layers': p_layers,
            'net': p_net,
            'netname': p_netname
        })

print(f"Total pads extracted: {len(pads)}")

# Count nets and connections
net_pads = {}
for p in pads:
    n = p['net']
    if n not in net_pads:
        net_pads[n] = []
    net_pads[n].append(p)

for n, plist in sorted(net_pads.items()):
    print(f"Net {n} ({plist[0]['netname'] if plist else ''}): {len(plist)} pads")

# Now check segments
segments = re.findall(r'\(segment\s+\(start\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(end\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(width\s+([\d\.\-]+)\)\s+\(layer\s+\"([^\"]+)\"\)\s+\(net\s+(\d+)\)\)', text)
print(f"Total segments: {len(segments)}")
for s in segments:
    print(f"Segment: start=({s[0]}, {s[1]}), end=({s[2]}, {s[3]}), layer={s[5]}, net={s[6]}")
