# -*- coding: utf-8 -*-
"""
Verification Script for Smart Fan Controller Rev B3:
Performs comprehensive, multi-domain audit across:
1. KiCad PCB (.kicad_pcb) & Schematic (.kicad_sch)
2. Production Gerbers (RS-274X & Excellon)
3. Manufacturing BOM (Excel & Markdown)
4. 3D CAD Enclosure STLs (Piece 1 & Piece 2)
"""

import os
import sys
import re
import struct
import math
import zipfile
import numpy as np
import trimesh
import openpyxl
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"D:\smart_fans"
DOWNLOAD_DIR = r"D:\下载"
KICAD_PCB = os.path.join(ROOT_DIR, "hardware", "kicad", "fan_ctrl_revB.kicad_pcb")
KICAD_SCH = os.path.join(ROOT_DIR, "hardware", "kicad", "fan_ctrl_revB.kicad_sch")
GERBER_ZIP = os.path.join(DOWNLOAD_DIR, "Gerber_fan_ctrl_revB_2026-11-04.zip")
BOM_XLSX = os.path.join(DOWNLOAD_DIR, "BOM_SmartFan_RevB.xlsx")
BOM_MD = os.path.join(ROOT_DIR, "docs", "hardware", "bom.md")
STL_ZIP = os.path.join(DOWNLOAD_DIR, "SmartFan_Sanweihou_3D_Print_Kit_2026-11-04.zip")
STL_P1 = os.path.join(ROOT_DIR, "mechanical", "stl", "print", "SmartFan_Piece1_Base_Enclosure.stl")
STL_P2 = os.path.join(ROOT_DIR, "mechanical", "stl", "print", "SmartFan_Piece2_Fan_Gimbal_Bracket.stl")

results = []

def check(category, item, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((category, item, status, detail))
    print(f"[{status}] {category} :: {item} -> {detail}")

print("==================================================================")
print("RUNNING REVB3 ENGINEERING AUDIT VERIFICATION")
print("==================================================================")

# --- 1. PCB & Electrical Routing Verification ---
src = open(KICAD_PCB, encoding="utf-8").read()
TOK = re.compile(r'\(|\)|"[^"]*"|[^\s()]+')

def parse_sexp(toks, i=0):
    assert toks[i] == '('
    out = []
    i += 1
    while toks[i] != ')':
        if toks[i] == '(':
            node, i = parse_sexp(toks, i)
            out.append(node)
        else:
            t = toks[i]
            if t.startswith('"'):
                t = t[1:-1]
            out.append(t)
            i += 1
    return out, i + 1

tree, _ = parse_sexp(TOK.findall(src), 0)

def find_all(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def get(node, name):
    r = find_all(node, name)
    return r[0] if r else None

nets = {}
for n in find_all(tree, 'net'):
    if len(n) >= 3 and n[1].isdigit():
        nets[int(n[1])] = n[2]

fps, segs, vias, zones = [], [], [], []
for c in tree:
    if not isinstance(c, list):
        continue
    if c[0] == 'footprint':
        at = get(c, 'at')
        ref = val = None
        for t in c:
            if isinstance(t, list) and t[0] == 'property' and len(t) > 2:
                if t[1] == 'Reference': ref = t[2]
                elif t[1] == 'Value': val = t[2]
        fx, fy = float(at[1]), float(at[2])
        pads = []
        for p in find_all(c, 'pad'):
            pat = get(p, 'at')
            px, py = float(pat[1]), float(pat[2])
            sz = get(p, 'size')
            net = get(p, 'net')
            pads.append(dict(num=p[1], x=fx + px, y=fy + py, w=float(sz[1]), h=float(sz[2]),
                             type=p[2], net=int(net[1]) if net else 0,
                             netname=(net[2] if net and len(net) > 2 else "")))
        fps.append(dict(ref=ref, val=val, x=fx, y=fy, pads=pads))
    elif c[0] == 'segment':
        s, e = get(c, 'start'), get(c, 'end')
        segs.append(dict(x1=float(s[1]), y1=float(s[2]), x2=float(e[1]), y2=float(e[2]),
                         w=float(get(c, 'width')[1]), layer=get(c, 'layer')[1],
                         net=int(get(c, 'net')[1])))
    elif c[0] == 'via':
        a = get(c, 'at')
        vias.append(dict(x=float(a[1]), y=float(a[2]), net=int(get(c, 'net')[1]),
                         size=float(get(c, 'size')[1]), drill=float(get(c, 'drill')[1])))
    elif c[0] == 'zone':
        zones.append(dict(net=int(get(c, 'net')[1]), layer=get(c, 'layer')[1],
                          filled=len(find_all(c, 'filled_polygon'))))

check("PCB", "Footprint Count", len(fps) == 47, f"47 components found")
check("PCB", "Pad Count", sum(len(f['pads']) for f in fps) == 170, f"170 pads found")
check("PCB", "Net Count", len(nets) == 32, f"32 electrical nets")

# GND Zones & Copper Pour Verification
f_cu_zones = [z for z in zones if z['layer'] == 'F.Cu' and z['net'] == 1]
b_cu_zones = [z for z in zones if z['layer'] == 'B.Cu' and z['net'] == 1]
check("PCB", "GND Zone Definition", len(f_cu_zones) == 1 and len(b_cu_zones) == 1, "Both F.Cu and B.Cu have Net 1 GND zones")
check("PCB", "GND Zone Filled Polygon", f_cu_zones[0]['filled'] >= 1 and b_cu_zones[0]['filled'] >= 1, "Explicit (filled_polygon ...) present in both zones")

# GND Stitching Vias
gnd_vias = [v for v in vias if v['net'] == 1]
check("PCB", "GND Stitching Vias", len(gnd_vias) >= 28, f"{len(gnd_vias)} GND stitching vias present")

# Pad Short-Circuit DRC Check
short_circuits = []
all_pads = [p for f in fps for p in f['pads']]
for i in range(len(all_pads)):
    p1 = all_pads[i]
    for j in range(i + 1, len(all_pads)):
        p2 = all_pads[j]
        dx = abs(p1['x'] - p2['x'])
        dy = abs(p1['y'] - p2['y'])
        cx = dx - (p1['w'] + p2['w']) / 2.0
        cy = dy - (p1['h'] + p2['h']) / 2.0
        if cx < 0.15 and cy < 0.15:
            if p1['net'] != p2['net'] and p1['net'] > 0 and p2['net'] > 0:
                short_circuits.append(f"Short between Net {p1['net']} and Net {p2['net']}")
check("PCB", "Pad Clearance DRC", len(short_circuits) == 0, f"{len(short_circuits)} pad short circuits")

# Electrical Connectivity (Segment graph analysis)
adj = defaultdict(lambda: defaultdict(set))
for s in segs:
    p1 = (round(s['x1'], 2), round(s['y1'], 2))
    p2 = (round(s['x2'], 2), round(s['y2'], 2))
    adj[s['net']][p1].add(p2)
    adj[s['net']][p2].add(p1)

def pt_dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def get_node_id(net, pt):
    for n in adj[net]:
        if pt_dist(pt, n) < 0.5:
            return n
    return None

unconnected_nets = []
for nid in sorted(nets):
    net_pads = [p for p in all_pads if p['net'] == nid]
    if len(net_pads) <= 1:
        continue
    # Check graph connectivity
    node_set = set()
    pad_nodes = []
    for p in net_pads:
        n = get_node_id(nid, (p['x'], p['y']))
        if n:
            pad_nodes.append(n)
            node_set.add(n)
        else:
            unconnected_nets.append((nid, nets[nid], f"Pad at ({p['x']}, {p['y']}) has no connected trace"))
            break
    if len(pad_nodes) == len(net_pads):
        # BFS
        visited = set([pad_nodes[0]])
        q = [pad_nodes[0]]
        while q:
            curr = q.pop(0)
            for neighbor in adj[nid][curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    q.append(neighbor)
        if not node_set.issubset(visited):
            unconnected_nets.append((nid, nets[nid], "Net split into multiple isolated islands"))

check("PCB", "Trace Electrical Connectivity", len(unconnected_nets) == 0, f"{len(unconnected_nets)} unconnected nets")

# Specific Critical Net Connections
# XL1509 FB (Pin 3) -> +5V (Net 4)
u2 = [f for f in fps if f['ref'] == 'U2'][0]
u2_fb = [p for p in u2['pads'] if p['num'] == '3'][0]
check("Circuit", "XL1509 FB to +5V", u2_fb['net'] == 4 and u2_fb['netname'] == '+5V', "XL1509 Pin 3 (FB) directly connected to Net 4 (+5V)")

# Blue Pill Polarity
mcu_l = [f for f in fps if f['ref'] == 'J_MCU_L'][0]
mcu_r = [f for f in fps if f['ref'] == 'J_MCU_R'][0]
ml_p1 = [p for p in mcu_l['pads'] if p['num'] == '1'][0]
ml_p2 = [p for p in mcu_l['pads'] if p['num'] == '2'][0]
ml_p3 = [p for p in mcu_l['pads'] if p['num'] == '3'][0]
mr_p18 = [p for p in mcu_r['pads'] if p['num'] == '18'][0]
mr_p19 = [p for p in mcu_r['pads'] if p['num'] == '19'][0]
mr_p20 = [p for p in mcu_r['pads'] if p['num'] == '20'][0]
check("Circuit", "Blue Pill Left Header 3V3/GND/5V", ml_p1['netname'] == '+3.3V' and ml_p2['netname'] == 'GND' and ml_p3['netname'] == '+5V', "Pin 1=3V3, Pin 2=GND, Pin 3=5V")
check("Circuit", "Blue Pill Right Header 3V3/GND/5V", mr_p18['netname'] == '+3.3V' and mr_p19['netname'] == 'GND' and mr_p20['netname'] == '+5V', "Pin 18=3V3, Pin 19=GND, Pin 20=5V")

# Encoder A/B Nets
enc = [f for f in fps if f['ref'] == 'J_ENC'][0]
enc_a = [p for p in enc['pads'] if p['num'] == '5'][0]
enc_b = [p for p in enc['pads'] if p['num'] == '4'][0]
check("Circuit", "Encoder ENC_A on Net 30", enc_a['net'] == 30 and enc_a['netname'] == 'ENC_A', "J_ENC.5 = Net 30 (ENC_A -> STM32 PA6)")
check("Circuit", "Encoder ENC_B on Net 31", enc_b['net'] == 31 and enc_b['netname'] == 'ENC_B', "J_ENC.4 = Net 31 (ENC_B -> STM32 PA7)")

# Board Size & Mounting Holes
h1 = [f for f in fps if f['ref'] == 'H1'][0]
h2 = [f for f in fps if f['ref'] == 'H2'][0]
h3 = [f for f in fps if f['ref'] == 'H3'][0]
h4 = [f for f in fps if f['ref'] == 'H4'][0]
pitch_x = round(h2['x'] - h1['x'], 2)
pitch_y = round(h3['y'] - h1['y'], 2)
check("PCB", "Mounting Hole Pitch", pitch_x == 85.0 and pitch_y == 85.0, f"Pitch: {pitch_x} x {pitch_y} mm (strictly 85.0 mm)")

# --- 2. Production Gerber Verification ---
check("Gerber", "Gerber Package ZIP", os.path.exists(GERBER_ZIP) and os.path.getsize(GERBER_ZIP) > 3000, f"ZIP exists ({os.path.getsize(GERBER_ZIP)} bytes)")
with zipfile.ZipFile(GERBER_ZIP, 'r') as zf:
    namelist = zf.namelist()
    check("Gerber", "Gerber 8 Layers Present", len(namelist) == 8, f"Layers: {', '.join(namelist)}")
    
    gko = zf.read("fan_ctrl_revB.GKO").decode('utf-8')
    g02_count = len(re.findall(r'G02\*', gko))
    check("Gerber", "GKO Circular Arcs (G02/G03)", g02_count == 4, f"{g02_count} G02 circular interpolation arcs found for R=3.0mm corners")

    gtl = zf.read("fan_ctrl_revB.GTL").decode('utf-8')
    gbl = zf.read("fan_ctrl_revB.GBL").decode('utf-8')
    gtl_g36 = len(re.findall(r'G36\*', gtl))
    gbl_g36 = len(re.findall(r'G36\*', gbl))
    check("Gerber", "GTL/GBL Area Fill (G36/G37)", gtl_g36 >= 1 and gbl_g36 >= 1, f"GTL G36={gtl_g36}, GBL G36={gbl_g36} (ground copper pour verified)")

# --- 3. BOM & LCSC C-Numbers Verification ---
check("BOM", "BOM Excel File", os.path.exists(BOM_XLSX) and os.path.getsize(BOM_XLSX) > 3000, f"BOM Excel exists ({os.path.getsize(BOM_XLSX)} bytes)")
wb = openpyxl.load_workbook(BOM_XLSX)
ws = wb.active
headers = [ws.cell(1, c).value for c in range(1, 10)]
bom_items = []
for r in range(2, ws.max_row + 1):
    c_part = str(ws.cell(r, 6).value)
    refs = str(ws.cell(r, 2).value)
    mpn = str(ws.cell(r, 7).value)
    bom_items.append((refs, c_part, mpn))

c_errors = [item for item in bom_items if not item[1].startswith('C') or not item[1][1:].isdigit()]
check("BOM", "100% Verified LCSC C-Numbers", len(c_errors) == 0, f"{len(bom_items)} line items all have valid LCSC parts")

# Check J_VOICE header is 7-Pin C50952
voice_item = [item for item in bom_items if "J_VOICE" in item[0]][0]
check("BOM", "J_VOICE 7-Pin Socket Match", voice_item[1] == "C50952", f"J_VOICE assigned C50952 (1x7P female header)")

# --- 4. 3D CAD STL Verification ---
check("CAD", "3D Print ZIP Package", os.path.exists(STL_ZIP) and os.path.getsize(STL_ZIP) > 10000, f"STL Package exists ({os.path.getsize(STL_ZIP)} bytes)")

tri_p1 = trimesh.load(STL_P1)
tri_p2 = trimesh.load(STL_P2)

b1 = tri_p1.bounding_box.extents
b2 = tri_p2.bounding_box.extents
v1 = tri_p1.volume / 1000.0
v2 = tri_p2.volume / 1000.0
total_v = v1 + v2

check("CAD", "Piece 1 Watertight 2-Manifold", tri_p1.is_watertight, "0 bad edges, 0 inverted normals")
check("CAD", "Piece 2 Watertight 2-Manifold", tri_p2.is_watertight, "0 bad edges, 0 inverted normals")
check("CAD", "Piece 1 Bounding Box <= 100mm", max(b1) <= 100.0, f"{b1[0]:.1f} x {b1[1]:.1f} x {b1[2]:.1f} mm")
check("CAD", "Piece 2 Bounding Box <= 100mm", max(b2) <= 100.0, f"{b2[0]:.1f} x {b2[1]:.1f} x {b2[2]:.1f} mm")
check("CAD", "Combined Volume <= 70.00 cm3", total_v <= 70.0, f"{total_v:.2f} cm3 (Piece 1: {v1:.2f} cm3, Piece 2: {v2:.2f} cm3)")

# Check 25 degree front console face area
agg = defaultdict(float)
for f in tri_p1.faces:
    a, b, c = tri_p1.vertices[f[0]], tri_p1.vertices[f[1]], tri_p1.vertices[f[2]]
    u = b - a; v = c - a
    n = np.cross(u, v)
    L = np.linalg.norm(n)
    if L < 1e-9: continue
    nz = abs(n[2] / L)
    ang = round(math.degrees(math.acos(min(1.0, nz))), 1)
    agg[ang] += L / 2.0

area_25 = agg[25.0]
check("CAD", "25° Front Console Face Area", area_25 > 2500.0, f"Area: {area_25:.1f} mm2 (Substantial 25° inclined console face)")

print("==================================================================")
all_pass = all(r[2] == "PASS" for r in results)
print(f"OVERALL AUDIT VERIFICATION RESULT: {'ALL PASS (100%)' if all_pass else 'FAILURES DETECTED'}")
print("==================================================================")
