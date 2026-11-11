import re, math, sys

def tokenize(s):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)

def parse(tokens):
    it = iter(tokens)
    def rec():
        node = []
        for tok in it:
            if tok == '(':
                node.append(rec())
            elif tok == ')':
                return node
            else:
                node.append(tok)
        return node
    out = []
    for tok in it:
        if tok == '(':
            out.append(rec())
        else:
            out.append(tok)
    return out

def head(n):
    return n[0] if isinstance(n, list) and n and isinstance(n[0], str) else None

def children(n, name):
    return [c for c in n if isinstance(c, list) and head(c) == name]

def unq(s):
    return s[1:-1] if isinstance(s, str) and s.startswith('"') else s

SCH = "hardware/kicad/fan_ctrl_revB.kicad_sch"
src = open(SCH, encoding="utf-8").read()
root = parse(tokenize(src))[0]

# --- lib symbols ---
libs = {}
ls = children(root, "lib_symbols")
if ls:
    for sym in children(ls[0], "symbol"):
        name = unq(sym[1])
        pins = []
        def walk(n):
            for c in n:
                if not isinstance(c, list):
                    continue
                if head(c) == "pin":
                    at = children(c, "at")
                    num = children(c, "number")
                    if at:
                        pins.append((float(at[0][1]), float(at[0][2]), unq(num[0][1]) if num else "?"))
                else:
                    walk(c)
        walk(sym)
        libs[name] = pins

print("lib_symbols:", len(libs), " total pins:", sum(len(v) for v in libs.values()))

# --- instances ---
insts = []
for sym in children(root, "symbol"):
    lid = children(sym, "lib_id")
    if not lid:
        continue
    at = children(sym, "at")
    props = {unq(p[1]): unq(p[2]) for p in children(sym, "property") if len(p) > 2}
    insts.append(dict(ref=props.get("Reference", "?"), lib=unq(lid[0][1]),
                      x=float(at[0][1]), y=float(at[0][2]), rot=float(at[0][3]) if len(at[0]) > 3 else 0.0))

# --- wires / labels / junctions / no_connect ---
wires = []
for w in children(root, "wire"):
    pts = [float(v) for v in re.findall(r'[\d.\-]+', " ".join(str(x) for x in w[1][1:]))]
    xy = children(w, "pts")[0]
    coords = [(float(p[1]), float(p[2])) for p in children(xy, "xy")]
    if len(coords) == 2:
        wires.append(coords)

labels = []
for lb in children(root, "label"):
    at = children(lb, "at")
    labels.append((unq(lb[1]), float(at[0][1]), float(at[0][2])))

eps = set()
for a, b in wires:
    eps.add((round(a[0], 2), round(a[1], 2)))
    eps.add((round(b[0], 2), round(b[1], 2)))

print("instances:", len(insts), " wires:", len(wires), " labels:", len(labels))

# pin absolute position: KiCad schem Y axis points down; symbol pin lib coords have Y up -> negate
def pin_pos(x, y, rot, px, py):
    th = math.radians(rot)
    # rotate lib coords by rot (KiCad rotates counter-clockwise in lib space, then flips Y)
    rx = px * math.cos(th) - py * math.sin(th)
    ry = px * math.sin(th) + py * math.cos(th)
    return (x + rx, y + ry)

hit = 0
tot = 0
misses = []
for it in insts:
    base = libs.get(it["lib"])
    if base is None:
        cand = [k for k in libs if k.split(":")[-1] == it["lib"].split(":")[-1]]
        base = libs[cand[0]] if cand else []
    n = h = 0
    for px, py, num in base:
        X, Y = pin_pos(it["x"], it["y"], it["rot"], px, py)
        n += 1
        tot += 1
        ok = (round(X, 2), round(Y, 2)) in eps
        if ok:
            hit += 1
            h += 1
        else:
            misses.append((it["ref"], num, round(X, 2), round(Y, 2), it["lib"]))
    print(f"  {it['ref']:12s} {it['lib']:32s} {h}/{n}")
print(f"\npins on wire endpoints: {hit}/{tot}")

# nearest-endpoint distance for misses
if misses:
    d = []
    for ref, num, X, Y in misses[:0]:
        pass

# labels attached to wires?
lab_hit = sum(1 for t, x, y in labels if (round(x, 2), round(y, 2)) in eps)
print(f"labels on wire endpoints: {lab_hit}/{len(labels)}")

# label net names vs pcb
from collections import Counter
print("distinct label names:", len(set(t for t, _, _ in labels)))
