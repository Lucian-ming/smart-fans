import struct, sys, math
from collections import defaultdict

def load_stl(path):
    data = open(path, 'rb').read()
    n = struct.unpack('<I', data[80:84])[0]
    if 84 + 50 * n == len(data):
        tris = []
        for i in range(n):
            off = 84 + 50 * i
            vals = struct.unpack('<12f', data[off:off + 48])
            tris.append((vals[3:6], vals[6:9], vals[9:12]))
        return tris, 'binary'
    # ascii
    tris = []
    cur = []
    for line in data.decode('utf-8', 'replace').splitlines():
        p = line.split()
        if p and p[0] == 'vertex':
            cur.append(tuple(float(x) for x in p[1:4]))
            if len(cur) == 3:
                tris.append(tuple(cur))
                cur = []
    return tris, 'ascii'

def analyse(path):
    tris, kind = load_stl(path)
    print(f"\n=== {path} ({kind}) triangles={len(tris)} ===")
    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    print("bbox X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]  size %.2f x %.2f x %.2f" %
          (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
           max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    # weld vertices
    key = {}
    def vid(v):
        k = (round(v[0], 4), round(v[1], 4), round(v[2], 4))
        if k not in key:
            key[k] = len(key)
        return key[k]
    faces = []
    degenerate = 0
    for t in tris:
        a, b, c = vid(t[0]), vid(t[1]), vid(t[2])
        if a == b or b == c or a == c:
            degenerate += 1
            continue
        faces.append((a, b, c))
    # edges
    ec = defaultdict(int)
    dir_e = defaultdict(int)
    for a, b, c in faces:
        for u, v in ((a, b), (b, c), (c, a)):
            ec[(min(u, v), max(u, v))] += 1
            dir_e[(u, v)] += 1
    bad = [e for e, c in ec.items() if c != 2]
    flip = sum(1 for (u, v), c in dir_e.items() if c > 1)
    print(f"vertices={len(key)} faces={len(faces)} degenerate={degenerate}")
    print(f"non-manifold/boundary edges (count!=2): {len(bad)}")
    print(f"duplicate directed edges (normal flip): {flip}")
    # volume
    V = 0.0
    pos = {i: k for k, i in key.items()}
    for a, b, c in faces:
        ax, ay, az = pos[a]; bx, by, bz = pos[b]; cx, cy, cz = pos[c]
        V += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6.0
    print(f"signed volume = {V/1000.0:.3f} cm3  (abs {abs(V)/1000:.3f})")
    return tris, V

for p in [r"D:/下载/SmartFan_Piece1_Base_Enclosure.stl",
          r"D:/下载/SmartFan_Piece2_Fan_Gimbal_Bracket.stl"]:
    analyse(p)
