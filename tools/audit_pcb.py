# -*- coding: utf-8 -*-
"""Parse fan_ctrl_revB.kicad_pcb and dump structural facts for audit."""
import re, json, math, sys

PATH = r"D:/smart_fans/hardware/kicad/fan_ctrl_revB.kicad_pcb"
txt = open(PATH, encoding="utf-8").read()

# --- tiny s-expression parser ---
def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c == '(' or c == ')':
            yield c; i += 1
        elif c == '"':
            j = i + 1; buf = []
            while j < n:
                if s[j] == '\\' and j + 1 < n:
                    buf.append(s[j+1]); j += 2
                elif s[j] == '"':
                    break
                else:
                    buf.append(s[j]); j += 1
            yield ('STR', ''.join(buf)); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()':
                j += 1
            yield ('ATOM', s[i:j]); i = j

def parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            top = stack.pop()
            stack[-1].append(top)
        else:
            stack[-1].append(t[1])
    return stack[0]

tree = parse(tokenize(txt))
root = None
for node in tree:
    if isinstance(node, list) and node and node[0] == 'kicad_pcb':
        root = node
        break

def find_all(node, tag):
    out = []
    for c in node:
        if isinstance(c, list) and c and c[0] == tag:
            out.append(c)
    return out

def get(node, tag):
    for c in node:
        if isinstance(c, list) and c and c[0] == tag:
            return c
    return None

def f(x):
    try: return float(x)
    except: return None

# ---- board outline ----
edge = get(root, 'gr_line'), get(root, 'gr_arc')
edges = []
for c in root:
    if isinstance(c, list) and c and c[0] in ('gr_line','gr_arc','gr_rect','gr_circle','gr_poly'):
        edges.append(c)

print("=== BOARD OUTLINE PRIMITIVES ===")
xs, ys = [], []
segs = []
for e in edges:
    kind = e[0]
    lay = get(e, 'layer')
    layers = [l for l in e if isinstance(l, list) and l[0]=='layer']
    if not layers or layers[0][1] != 'Edge.Cuts':
        continue
    st = get(e, 'start'); en = get(e, 'end')
    if kind == 'gr_line' and st and en:
        x1, y1 = float(st[1]), float(st[2]); x2, y2 = float(en[1]), float(en[2])
        segs.append(((x1,y1),(x2,y2)))
        xs += [x1,x2]; ys += [y1,y2]
        print(f"SEC  {x1} {y1} -> {x2} {y2}")
    elif kind == 'gr_arc':
        print("ARC", e)
    elif kind == 'gr_rect':
        print("RECT", e)
print(f"\nEdge bbox: X[{min(xs)},{max(xs)}] Y[{min(ys)},{max(ys)}]  => {max(xs)-min(xs)} x {max(ys)-min(ys)} mm")

# closed outline check
print(f"segment count = {len(segs)}")

# ---- footprints ----
fps = find_all(root, 'footprint')
print(f"\n=== FOOTPRINTS ({len(fps)}) ===")
foot = []
for fp in fps:
    ref = val = None
    layer = get(fp, 'layer')
    at = get(fp, 'at')
    for c in fp:
        if isinstance(c, list) and c and c[0] == 'fp_text':
            if len(c) > 2 and c[1] in ('reference','value'):
                if c[1] == 'reference': ref = c[2]
                else: val = c[2]
    if ref is None:
        # properties
        for c in fp:
            if isinstance(c, list) and c and c[0] == 'property':
                if c[1] == 'Reference': ref = c[2]
                if c[1] == 'Value': val = c[2]
    pads = find_all(fp, 'pad')
    pinfo = []
    for p in pads:
        pat = get(p, 'at')
        net = get(p, 'net')
        size = get(p, 'size')
        ptype = p[2] if len(p) > 2 else '?'
        pshape = p[3] if len(p) > 3 else '?'
        pinfo.append(dict(num=p[1], type=ptype, shape=pshape,
                          x=float(pat[1]) if pat else None,
                          y=float(pat[2]) if pat else None,
                          rot=float(pat[3]) if pat and len(pat)>3 else 0.0,
                          net=net[1] if net and len(net)>1 else None,
                          netname=net[2] if net and len(net)>2 else None,
                          w=float(size[1]) if size else None,
                          h=float(size[2]) if size else None))
    foot.append(dict(ref=ref, val=val, layer=layer[1] if layer else None,
                     x=float(at[1]) if at else None, y=float(at[2]) if at else None,
                     rot=float(at[3]) if at and len(at)>3 else 0.0,
                     desc=(get(fp,'descr')[1] if get(fp,'descr') else ''),
                     pads=pinfo, raw=fp))

foot.sort(key=lambda d: (d['ref'] or ''))
print(f"{'REF':10s} {'VALUE':24s} {'LAYER':10s} {'X':>8s} {'Y':>8s} {'ROT':>6s} {'NPADS':>5s}")
for d in foot:
    print(f"{str(d['ref']):10s} {str(d['val'])[:24]:24s} {str(d['layer']):10s} {d['x']:8.2f} {d['y']:8.2f} {d['rot']:6.1f} {len(d['pads']):5d}")

# ---- tracks ----
segs_t = find_all(root, 'segment')
vias = find_all(root, 'via')
print(f"\n=== TRACKS: {len(segs_t)} segments, {len(vias)} vias ===")
tracknets = {}
for s in segs_t:
    net = get(s, 'net')
    nm = net[2] if net and len(net) > 2 else '?'
    tracknets[nm] = tracknets.get(nm, 0) + 1
for k, v in sorted(tracknets.items(), key=lambda kv: -kv[1]):
    print(f"  {k:16s} {v:4d}")
# layer distribution
laydist = {}
for s in segs_t:
    l = get(s, 'layer')
    laydist[l[1] if l else '?'] = laydist.get(l[1] if l else '?', 0) + 1
print("layers:", laydist)

zones = find_all(root, 'zone')
print(f"\n=== ZONES: {len(zones)} ===")
for z in zones:
    n = get(z, 'net_name'); l = get(z, 'layer')
    poly = get(z, 'polygon')
    pts = []
    if poly:
        for pt in find_all(poly, 'xy'):
            pts.append((float(pt[1]), float(pt[2])))
    print(f"  zone net={n[1] if n else '?'} layer={l[1] if l else '?'} pts={len(pts)}")

json.dump([{k: v for k, v in d.items() if k != 'raw'} for d in foot],
          open(r"D:/smart_fans/tools/footprints.json", "w", encoding="utf-8"), indent=1)
print("\nwrote tools/footprints.json")
