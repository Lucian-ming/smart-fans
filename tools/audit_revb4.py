import re, math, json, sys
import numpy as np

PCB = "hardware/kicad/fan_ctrl_revB.kicad_pcb"
src = open(PCB, encoding="utf-8").read()

def blocks(s, token):
    out = []
    for m in re.finditer(r'\(' + token + r'[ \n]', s):
        i = m.start(); d = 0
        for j in range(i, len(s)):
            if s[j] == '(':
                d += 1
            elif s[j] == ')':
                d -= 1
                if d == 0:
                    out.append(s[i:j+1]); break
    return out

def xy(block):
    return np.array([[float(a), float(b)] for a, b in re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', block)])

# ---------- nets ----------
nets = {}
for m in re.finditer(r'\n  \(net (\d+) "([^"]*)"\)', src):
    nets[int(m.group(1))] = m.group(2)

# ---------- footprints / pads ----------
pads = []   # dict: ref, num, x, y, shape, w, h, drill, net, rot, layer
fps = blocks(src, "footprint")
for fb in fps:
    ref = re.search(r'\(property "Reference" "([^"]+)"', fb) or re.search(r'\(fp_text reference "([^"]+)"', fb)
    ref = ref.group(1) if ref else "?"
    at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', fb)
    fx, fy = float(at.group(1)), float(at.group(2))
    frot = float(at.group(3)) if at.group(3) else 0.0
    for pb in blocks(fb, "pad"):
        num = re.match(r'\(pad "?([^" ]+)"?', pb)
        pa = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', pb)
        px, py = float(pa.group(1)), float(pa.group(2))
        prot = float(pa.group(3)) if pa.group(3) else 0.0
        sz = re.search(r'\(size ([\d.\-]+) ([\d.\-]+)\)', pb)
        w, h = float(sz.group(1)), float(sz.group(2))
        dr = re.search(r'\(drill ([\d.]+)\)', pb)
        shape = re.match(r'\(pad "?[^" ]+"? (\w+)', pb).group(1)
        nn = re.search(r'\(net (\d+) "([^"]*)"\)', pb)
        th = float(frot) * math.pi / 180
        # rotate footprint-local pad offset
        ax = fx + px * math.cos(th) - py * math.sin(th)
        ay = fy + px * math.sin(th) + py * math.cos(th)
        pads.append(dict(ref=ref, num=num.group(1), x=ax, y=ay, shape=shape, w=w, h=h,
                         drill=float(dr.group(1)) if dr else 0.0,
                         net=int(nn.group(1)) if nn else 0,
                         netname=nn.group(2) if nn else "",
                         rot=(frot + prot) % 360))

# ---------- zones ----------
zones = []
for zb in blocks(src, "zone"):
    nm = re.search(r'\(net_name "([^"]*)"\)', zb)
    lay = re.search(r'\(layer "([^"]*)"\)', zb)
    fill = blocks(zb, "filled_polygon")
    polys = []
    if fill:
        for pts in blocks(fill[0], "pts"):
            polys.append(xy(pts))
    zones.append(dict(net=nm.group(1) if nm else "?", layer=lay.group(1) if lay else "?",
                      polys=polys,
                      clearance=float((re.search(r'\(clearance ([\d.]+)\)', zb) or [0, 0.25])[1])))

# ---------- segments / vias ----------
segs = []
for sb in blocks(src, "segment"):
    a = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', sb)
    b = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', sb)
    w = re.search(r'\(width ([\d.]+)\)', sb)
    n = re.search(r'\(net (\d+)\)', sb)
    ly = re.search(r'\(layer "([^"]+)"\)', sb)
    segs.append(dict(x1=float(a.group(1)), y1=float(a.group(2)), x2=float(b.group(1)), y2=float(b.group(2)),
                     w=float(w.group(1)), net=int(n.group(1)), layer=ly.group(1)))
vias = []
for vb in blocks(src, "via"):
    a = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', vb)
    n = re.search(r'\(net (\d+)\)', vb)
    s = re.search(r'\(size ([\d.]+)\)', vb)
    d = re.search(r'\(drill ([\d.]+)\)', vb)
    vias.append(dict(x=float(a.group(1)), y=float(a.group(2)), net=int(n.group(1)),
                     size=float(s.group(1)), drill=float(d.group(1))))

# ---------- geometry helpers ----------
def pip(pt, poly):
    """ray casting, returns True if inside"""
    x, y = pt
    n = len(poly); inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-18) + xi):
            inside = not inside
        j = i
    return inside

def seg_dist(p, polys):
    best = 1e9
    for poly in polys:
        a = poly
        b = np.roll(poly, -1, axis=0)
        for i in range(len(a)):
            ax, ay = a[i]; bx, by = b[i]
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy
            t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * vx + (p[1] - ay) * vy) / L2))
            dx, dy = p[0] - (ax + t * vx), p[1] - (ay + t * vy)
            d = math.hypot(dx, dy)
            if d < best:
                best = d
    return best

def pad_clearance(pad, polys):
    """min distance from pad outline to polygon boundary; negative if pad center inside copper"""
    # sample pad outline points
    pts = []
    n = 24
    for k in range(n):
        th = 2 * math.pi * k / n
        c, s = math.cos(th), math.sin(th)
        if pad["shape"] == "circle":
            r = pad["w"] / 2
            pts.append((pad["x"] + r * c, pad["y"] + r * s))
        else:
            pts.append((pad["x"] + (pad["w"] / 2) * c, pad["y"] + (pad["h"] / 2) * s))
    inside = [pip(q, poly) for poly in polys for q in pts]
    d = min(seg_dist(q, polys) for q in pts)
    return (-1.0, d) if any(inside) else (1.0, d)

# ---------- report ----------
print("=== 基本情况 ===")
print("footprints", len(fps), " pads", len(pads), " segs", len(segs), " vias", len(vias), " zones", len(zones), " nets", len(nets))

# board bbox
edges = []
for kw in ["gr_line", "gr_arc"]:
    for b in blocks(src, kw):
        if '"Edge.Cuts"' not in b:
            continue
        for tag in ["start", "mid", "end", "center"]:
            m = re.search(r'\(%s ([\d.\-]+) ([\d.\-]+)\)' % tag, b)
            if m:
                edges.append((float(m.group(1)), float(m.group(2))))
E = np.array(edges)
print("Edge.Cuts bbox", E[:, 0].min(), E[:, 0].max(), E[:, 1].min(), E[:, 1].max(),
      "->", round(E[:, 0].max() - E[:, 0].min(), 2), "x", round(E[:, 1].max() - E[:, 1].min(), 2))

print("\n=== ZONE ===")
for z in zones:
    print(f"  {z['layer']:5s} net={z['net']} pts_blocks={len(z['polys'])} "
          f"verts={[len(p) for p in z['polys']][:6]} clearance={z['clearance']}")

print("\n=== 铺铜避让核验（非 GND 焊盘 → 铜边界距离）===")
gnd = [p for p in pads if p["netname"] == "GND"]
nongnd = [p for p in pads if p["netname"] != "GND"]
print(f"  GND 焊盘 {len(gnd)}  非 GND 焊盘 {len(nongnd)}")
worst = []
for z in zones:
    if not z["polys"]:
        continue
    for p in nongnd:
        # only pads present on that layer matter; assume THT on both, SMD on F.Cu
        sign, d = pad_clearance(p, z["polys"])
        worst.append((d, sign, p["ref"], p["num"], p["netname"], z["layer"]))
worst.sort()
print("  最危险 12 个 (距离 mm, 是否在铜内, ref.pad, net, layer):")
for w in worst[:12]:
    print(f"    {w[0]:7.3f} inCu={w[1]<0} {w[2]}.{w[3]:<3s} {w[4]:<14s} {w[5]}")
bad = [w for w in worst if w[1] < 0]
print(f"  => 落在铜内的非 GND 焊盘: {len(bad)}")
viol = [w for w in worst if 0 <= w[0] < 0.25]
print(f"  => 间隙 < 0.25mm: {len(viol)}")
if viol:
    for w in viol[:8]:
        print(f"     {w[0]:.3f} {w[2]}.{w[3]} {w[4]} {w[5]}")

print("\n=== 走线 / 过孔 ===")
print("  seg 总长 %.1f mm" % sum(math.hypot(s["x2"] - s["x1"], s["y2"] - s["y1"]) for s in segs))
from collections import Counter
print("  seg per net:", dict(Counter(s["net"] for s in segs)))
print("  vias per net:", dict(Counter(v["net"] for v in vias)))
print("  GND segs:", sum(1 for s in segs if s["net"] == 1), " GND vias:", sum(1 for v in vias if v["net"] == 1))
print("  width range", min(s["w"] for s in segs), max(s["w"] for s in segs))

# ---------- connectivity: union-find over pads+segs+vias endpoints ----------
print("\n=== 网络连通性（并查集）===")
parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb

# nodes: ('p', idx) pads, ('s', i, 0/1) segment endpoints, ('v', i) vias
for i, s in enumerate(segs):
    pass
def near_net(x, y, net, tol=0.35):
    """find pads/vias of same net within tol"""
    hits = []
    for k, p in enumerate(pads):
        if p["net"] == net and math.hypot(p["x"] - x, p["y"] - y) <= tol + p["w"] / 2:
            hits.append(('p', k))
    for k, v in enumerate(vias):
        if v["net"] == net and math.hypot(v["x"] - x, v["y"] - y) <= tol + v["size"] / 2:
            hits.append(('v', k))
    return hits

for i, s in enumerate(segs):
    a, b = ('se', i, 0), ('se', i, 1)
    union(a, b)
    for h in near_net(s["x1"], s["y1"], s["net"]):
        union(a, h)
    for h in near_net(s["x2"], s["y2"], s["net"]):
        union(b, h)

# merge segment endpoints that touch each other (same net, both layers ok via vias only... approximate: same layer)
for i, s in enumerate(segs):
    for j, t in enumerate(segs):
        if i >= j or s["net"] != t["net"]:
            continue
        for (px, py), (qx, qy) in [((s["x1"], s["y1"]), (s["x2"], s["y2"])), ]:
            pass

# simpler: treat nets as connected if all pads of a net are linked via segments graph
adj_pads = {n: [] for n in nets}
for i, s in enumerate(segs):
    for h in near_net(s["x1"], s["y1"], s["net"]):
        for h2 in near_net(s["x2"], s["y2"], s["net"]):
            union(h, h2)

# also same-point segments chain
pts_by_net = {}
for i, s in enumerate(segs):
    pts_by_net.setdefault(s["net"], []).append((('se', i, 0), (s["x1"], s["y1"])))
    pts_by_net.setdefault(s["net"], []).append((('se', i, 1), (s["x2"], s["y2"])))
for net, lst in pts_by_net.items():
    for a in range(len(lst)):
        for b in range(a + 1, len(lst)):
            if lst[a][1] != lst[b][1]:
                if math.hypot(lst[a][1][0] - lst[b][1][0], lst[a][1][1] - lst[b][1][1]) < 0.01:
                    union(lst[a][0], lst[b][0])

report = []
for n, name in nets.items():
    ps = [k for k, p in enumerate(pads) if p["net"] == n]
    vs = [k for k, v in enumerate(vias) if v["net"] == n]
    if len(ps) + len(vs) < 2:
        continue
    roots = set()
    for k in ps:
        roots.add(find(('p', k)))
    for k in vs:
        roots.add(find(('v', k)))
    report.append((n, name, len(ps), len(vs), len(roots)))
print(f"  {'net':>3} {'name':14s} {'pads':>4} {'vias':>4} {'islands':>7}")
for r in sorted(report):
    flag = "  <== 孤岛" if r[4] > 1 else ""
    print(f"  {r[0]:>3} {r[1]:14s} {r[2]:>4} {r[3]:>4} {r[4]:>7}{flag}")
print("  网络总数", len(report), " 有孤岛的网络", sum(1 for r in report if r[4] > 1))
