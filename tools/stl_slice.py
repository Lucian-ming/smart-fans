import struct, math
from collections import defaultdict

def load(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    tris = []
    for i in range(n):
        o = 84 + 50 * i
        v = struct.unpack('<12f', d[o:o + 48])
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris

def slice_z(tris, z):
    segs = []
    for a, b, c in tris:
        pts = []
        for p, q in ((a, b), (b, c), (c, a)):
            if (p[2] - z) * (q[2] - z) < 0:
                t = (z - p[2]) / (q[2] - p[2])
                pts.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
            elif abs(p[2] - z) < 1e-9:
                pts.append((p[0], p[1]))
            elif abs(q[2] - z) < 1e-9:
                pts.append((q[0], q[1]))
        # dedupe
        u = []
        for p in pts:
            if not any(math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-6 for q in u):
                u.append(p)
        if len(u) == 2:
            segs.append(tuple(u))
    return segs

def chain(segs):
    # build adjacency on rounded points
    def k(p): return (round(p[0], 3), round(p[1], 3))
    adj = defaultdict(list)
    for i, (p, q) in enumerate(segs):
        adj[k(p)].append((i, q)); adj[k(q)].append((i, p))
    used = [False] * len(segs)
    loops = []
    for i in range(len(segs)):
        if used[i]:
            continue
        used[i] = True
        p, q = segs[i]
        loop = [p, q]
        cur = q
        while True:
            nxt = None
            for (j, o) in adj[k(cur)]:
                if not used[j]:
                    nxt = (j, o); break
            if not nxt:
                break
            used[nxt[0]] = True
            cur = nxt[1]
            loop.append(cur)
        if len(loop) > 2:
            loops.append(loop)
    return loops

def area(loop):
    s = 0
    for i in range(len(loop)):
        x1, y1 = loop[i]; x2, y2 = loop[(i + 1) % len(loop)]
        s += x1 * y2 - x2 * y1
    return s / 2

P1 = load(r"D:/下载/SmartFan_Piece1_Base_Enclosure.stl")
for z in (1.0, 2.0, 4.0, 6.0, 10.0, 20.0, 26.0):
    loops = chain(slice_z(P1, z))
    print(f"\n--- Piece1 slice z={z} : {len(loops)} loops ---")
    for L in sorted(loops, key=lambda l: -abs(area(l)))[:8]:
        xs = [p[0] for p in L]; ys = [p[1] for p in L]
        print(f"   bbox X[{min(xs):7.2f},{max(xs):7.2f}] Y[{min(ys):7.2f},{max(ys):7.2f}]  "
              f"size {max(xs)-min(xs):6.2f}x{max(ys)-min(ys):6.2f}  area {abs(area(L)):9.2f} mm2  n={len(L)}")

# face normal statistics: find the tilted front panel
print("\n--- Piece1 tilted faces (normal from vertical) ---")
agg = defaultdict(float)
for a, b, c in P1:
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    L = math.sqrt(sum(x * x for x in n))
    if L < 1e-9:
        continue
    n = [x / L for x in n]
    ang = math.degrees(math.acos(min(1, abs(n[2]))))
    A = L / 2
    agg[round(ang, 1)] += A
for a, A in sorted(agg.items(), key=lambda kv: -kv[1])[:8]:
    print(f"   normal tilt {a:5.1f} deg : area {A:9.1f} mm2")
