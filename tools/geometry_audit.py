# -*- coding: utf-8 -*-
"""Geometry + connectivity audit of fan_ctrl_revB."""
import json, math, re
import numpy as np

FP = json.load(open(r"D:/smart_fans/tools/footprints.json", encoding="utf-8"))
PCB = r"D:/smart_fans/hardware/kicad/fan_ctrl_revB.kicad_pcb"
txt = open(PCB, encoding="utf-8").read()

# footprints.json pad coords are LOCAL to footprint; convert to global
for f in FP:
    for p in f["pads"]:
        p["gx"] = f["x"] + p["x"]
        p["gy"] = f["y"] + p["y"]

# board local origin (100,100), 98x98, chamfer 3mm
def loc(v): return v - 100.0

print("="*70)
print("1) MOUNTING HOLE KEEPOUT (r=4.5mm, centres at local 5/93)")
holes = {"H1": (5, 5), "H2": (93, 5), "H3": (5, 93), "H4": (93, 93)}
worst = []
for hname, (hx, hy) in holes.items():
    rows = []
    for f in FP:
        for p in f["pads"]:
            if f["ref"] == hname: continue
            px, py = loc(p["gx"]), loc(p["gy"])
            r = 0.5 * math.hypot(p["w"], p["h"])   # conservative: half-diagonal
            d = math.hypot(px - hx, py - hy) - r
            rows.append((d, f"pad {f['ref']}.{p['num']}"))
        # silk bbox corners from raw fp_line
        xs, ys = [], []
        for c in []:
            if isinstance(c, list) and c and c[0] == "fp_line":
                st = next((q for q in c if isinstance(q, list) and q[0] == "start"), None)
                en = next((q for q in c if isinstance(q, list) and q[0] == "end"), None)
                if st and en:
                    xs += [f["x"] + float(st[1]), f["x"] + float(en[1])]
                    ys += [f["y"] + float(st[2]), f["y"] + float(en[2])]
        if xs:
            for cx in (min(xs), max(xs)):
                for cy in (min(ys), max(ys)):
                    d = math.hypot(loc(cx) - hx, loc(cy) - hy)
                    rows.append((d, f"body {f['ref']} corner"))
    rows.sort()
    print(f"\n  {hname} center ({hx},{hy}): closest 5 objects")
    for d, what in rows[:5]:
        flag = "  <-- VIOLATION" if d < 4.5 else ""
        print(f"     {d:6.2f} mm  {what}{flag}")

# tracks vs holes
segs = re.findall(r"\(segment \(start ([\d.]+) ([\d.]+)\) \(end ([\d.]+) ([\d.]+)\) \(width ([\d.]+)\) \(layer \"([^\"]+)\"\) \(net (\d+)\)", txt)
print(f"\n  track segments parsed: {len(segs)}")

def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-x1)*dx+(py-y1)*dy)/L2))
    return math.hypot(px-(x1+t*dx), py-(y1+t*dy))

for hname, (hx, hy) in holes.items():
    best = (99, None)
    for s in segs:
        x1,y1,x2,y2,w = map(float, s[:5])
        d = seg_dist(hx+100, hy+100, x1,y1,x2,y2) - w/2
        if d < best[0]: best = (d, s)
    print(f"  {hname}: nearest track edge {best[0]:.2f} mm")

print("\n" + "="*70)
print("2) PAD-TO-PAD CLEARANCE < 0.20mm on DIFFERENT nets (same layer)")
pads = []
for f in FP:
    for p in f["pads"]:
        pads.append(dict(ref=f["ref"], num=p["num"], x=p["gx"], y=p["gy"],
                         w=p["w"], h=p["h"], net=p["net"], t=p["type"]))
bad = []
for i in range(len(pads)):
    for j in range(i+1, len(pads)):
        a, b = pads[i], pads[j]
        if False: continue
        if int(a["net"] or 0) == int(b["net"] or 0) and int(a["net"] or 0) != 0: continue
        gx = abs(a["x"]-b["x"]) - (a["w"]+b["w"])/2
        gy = abs(a["y"]-b["y"]) - (a["h"]+b["h"])/2
        gap = max(gx, gy)
        if gap < 0.20:
            bad.append((gap, a["ref"], a["num"], a["net"], b["ref"], b["num"], b["net"]))
bad.sort()
print(f"  violations: {len(bad)}")
for g, ra, na, neta, rb, nb, netb in bad[:15]:
    print(f"    gap {g:+.2f} mm  {ra}.{na}(net{neta}) vs {rb}.{nb}(net{netb})")

print("\n" + "="*70)
print("3) PADS / BODY OUTSIDE 98x98 BOARD")
for f in FP:
    for p in f["pads"]:
        x, y = loc(p["gx"]), loc(p["gy"])
        if x < 0 or x > 98 or y < 0 or y > 98:
            print(f"  OUT: {f['ref']}.{p['num']} at ({x:.2f},{y:.2f})")

print("\n" + "="*70)
print("4) CONNECTIVITY: pads per net vs copper segments per net")
netpads = {}
for f in FP:
    for p in f["pads"]:
        netpads.setdefault(int(p["net"] or 0), []).append(f"{f['ref']}.{p['num']}")
segnet = {}
for s in segs:
    segnet[int(s[6])] = segnet.get(int(s[6]), 0) + 1

names = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', txt))
print(f"  {'code':>4} {'name':16s} {'pads':>5} {'segs':>5}  routed?")
total_open = 0
for code in sorted(netpads, key=lambda z:int(z)):
    n = len(netpads[code]); s = segnet.get(int(code), 0)
    nm = names.get(str(code), "?")
    status = "copper" if s else "NO COPPER"
    if s == 0 and n >= 2: total_open += 1
    print(f"  {int(code):4d} {nm:16s} {n:5d} {s:5d}  {status}")
print(f"\n  nets with >=2 pads but ZERO copper: {total_open}")
print(f"  total copper segments: {len(segs)}   vias: {txt.count('(via')}   zones: {txt.count('(zone')}   models: {txt.count('(model')}")

print("\n" + "="*70)
print("5) NET 0 sanity")
print(f"  (net 0 ...) declarations: {re.findall(r'\(net 0 \"([^\"]*)\"\)', txt)[:5]}")
print(f"  pads on net 0: {len(netpads.get(0,[]))}")
