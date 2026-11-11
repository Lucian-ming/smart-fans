import re, json, math
from collections import defaultdict

SRC = "hardware/kicad/fan_ctrl_revB.kicad_pcb"
src = open(SRC, encoding="utf-8").read()

TOK = re.compile(r'\(|\)|"[^"]*"|[^\s()]+')

def parse(toks, i=0):
    assert toks[i] == '('
    out = []
    i += 1
    while toks[i] != ')':
        if toks[i] == '(':
            node, i = parse(toks, i)
            out.append(node)
        else:
            t = toks[i]
            if t.startswith('"'):
                t = t[1:-1]
            out.append(t)
            i += 1
    return out, i + 1

tree, _ = parse(TOK.findall(src), 0)

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
        lcsc = mpn = None
        for t in c:
            if isinstance(t, list) and t[0] == 'fp_text' and t[1] == 'reference':
                ref = t[2]
            if isinstance(t, list) and t[0] == 'fp_text' and t[1] == 'value':
                val = t[2]
            if isinstance(t, list) and t[0] == 'property' and len(t) > 2:
                if t[1] == 'Reference':
                    ref = t[2]
                elif t[1] == 'Value':
                    val = t[2]
                elif t[1] == 'LCSC':
                    lcsc = t[2]
                elif t[1] == 'MPN':
                    mpn = t[2]
        fx, fy = float(at[1]), float(at[2])
        frot = float(at[3]) if len(at) > 3 else 0.0
        pads = []
        for p in find_all(c, 'pad'):
            pat = get(p, 'at')
            px, py = float(pat[1]), float(pat[2])
            sz = get(p, 'size')
            net = get(p, 'net')
            dr = get(p, 'drill')
            pads.append(dict(num=p[1], x=fx + px, y=fy + py, dx=px, dy=py,
                             w=float(sz[1]), h=float(sz[2]), type=p[2], shape=p[3],
                             net=int(net[1]) if net else 0,
                             netname=(net[2] if net and len(net) > 2 else ""),
                             drill=(float(dr[1]) if dr and dr[1] != 'oval' else 0.0)))
        fps.append(dict(ref=ref, val=val, x=fx, y=fy, rot=frot, lib=c[1], pads=pads, lcsc=lcsc, mpn=mpn))
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

print("== BOARD ==")
print("footprints", len(fps), "pads", sum(len(f['pads']) for f in fps),
      "segs", len(segs), "vias", len(vias))
for z in zones:
    print("zone", z)
xs = [p['x'] for f in fps for p in f['pads']]
ys = [p['y'] for f in fps for p in f['pads']]
print("pad bbox x[%.3f,%.3f] y[%.3f,%.3f]" % (min(xs), max(xs), min(ys), max(ys)))

pd = defaultdict(list)
for f in fps:
    for p in f['pads']:
        pd[p['net']].append((f['ref'], p['num'], p['netname']))
sd = defaultdict(int)
vd = defaultdict(int)
for s in segs:
    sd[s['net']] += 1
for v in vias:
    vd[v['net']] += 1

print("\n== NETS ==")
for n in sorted(nets):
    print("net %2d %-14s pads=%3d segs=%3d vias=%2d" % (n, nets[n], len(pd[n]), sd[n], vd[n]))
print("net0 pads:", len(pd[0]))

def pt_seg_dist(px, py, s):
    x1, y1, x2, y2 = s['x1'], s['y1'], s['x2'], s['y2']
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

class UF:
    def __init__(self, n):
        self.p = list(range(n))
    def f(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a
    def u(self, a, b):
        ra, rb = self.f(a), self.f(b)
        if ra != rb:
            self.p[rb] = ra

report = []
for n in sorted(nets):
    pads = [(f, p) for f in fps for p in f['pads'] if p['net'] == n]
    S = [s for s in segs if s['net'] == n]
    V = [v for v in vias if v['net'] == n]
    if len(pads) < 2:
        continue
    nodes = [('p', i) for i in range(len(pads))] + [('s', i) for i in range(len(S))] + [('v', i) for i in range(len(V))]
    idx = {k: i for i, k in enumerate(nodes)}
    uf = UF(len(nodes))
    TOL = 0.05
    for i, s in enumerate(S):
        for (ex, ey) in ((s['x1'], s['y1']), (s['x2'], s['y2'])):
            for j, (f, p) in enumerate(pads):
                if math.hypot(ex - p['x'], ey - p['y']) < TOL + max(p['w'], p['h']) / 2:
                    uf.u(idx[('s', i)], idx[('p', j)])
            for k, v in enumerate(V):
                if math.hypot(ex - v['x'], ey - v['y']) < TOL:
                    uf.u(idx[('s', i)], idx[('v', k)])
            for j2, s2 in enumerate(S):
                if j2 == i:
                    continue
                for (fx2, fy2) in ((s2['x1'], s2['y1']), (s2['x2'], s2['y2'])):
                    if math.hypot(ex - fx2, ey - fy2) < TOL:
                        uf.u(idx[('s', i)], idx[('s', j2)])
    for i, s in enumerate(S):
        for j, (f, p) in enumerate(pads):
            if pt_seg_dist(p['x'], p['y'], s) < max(p['w'], p['h']) / 2 + s['w'] / 2:
                uf.u(idx[('s', i)], idx[('p', j)])
    for k, v in enumerate(V):
        for j, (f, p) in enumerate(pads):
            if math.hypot(v['x'] - p['x'], v['y'] - p['y']) < TOL + max(p['w'], p['h']) / 2:
                uf.u(idx[('v', k)], idx[('p', j)])
    comps = defaultdict(list)
    for j, (f, p) in enumerate(pads):
        comps[uf.f(idx[('p', j)])].append(f"{f['ref']}.{p['num']}")
    if len(comps) > 1:
        report.append((n, nets[n], sorted(comps.values(), key=len, reverse=True)))

print("\n== UNCONNECTED NETS (pads split into >1 island) ==")
for n, nm, cs in report:
    print(f"net {n:2d} {nm:14s} islands={len(cs)}  " + " | ".join(",".join(c) for c in cs))

json.dump(dict(fps=fps, segs=segs, vias=vias, zones=zones, nets=nets),
          open("tools/revb2.json", "w"), ensure_ascii=False)
print("\nsaved tools/revb2.json")
