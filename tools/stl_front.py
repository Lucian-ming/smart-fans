import struct, math
from collections import defaultdict

def load(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    out = []
    for i in range(n):
        v = struct.unpack('<12f', d[84 + 50 * i:84 + 50 * i + 48])
        out.append((v[3:6], v[6:9], v[9:12]))
    return out

T = load(r"D:/下载/SmartFan_Piece1_Base_Enclosure.stl")

def slice_plane(tris, axis, val):
    segs = []
    for a, b, c in tris:
        pts = []
        for p, q in ((a, b), (b, c), (c, a)):
            if (p[axis] - val) * (q[axis] - val) < 0:
                t = (val - p[axis]) / (q[axis] - p[axis])
                pts.append(tuple(p[i] + t * (q[i] - p[i]) for i in range(3)))
            elif abs(p[axis] - val) < 1e-9:
                pts.append(tuple(p))
            elif abs(q[axis] - val) < 1e-9:
                pts.append(tuple(q))
        u = []
        for p in pts:
            if not any(math.dist(p, q) < 1e-6 for q in u):
                u.append(p)
        if len(u) == 2:
            segs.append(u)
    # project to other two axes
    ax = [i for i in range(3) if i != axis]
    return [tuple((s[0][ax[0]], s[0][ax[1]], s[1][ax[0]], s[1][ax[1]])) for s in segs], ax

def chain2(segs):
    adj = defaultdict(list)
    def k(p): return (round(p[0], 3), round(p[1], 3))
    for i, (x1, y1, x2, y2) in enumerate(segs):
        adj[k((x1, y1))].append((i, (x2, y2)))
        adj[k((x2, y2))].append((i, (x1, y1)))
    used = [False] * len(segs)
    loops = []
    for i, (x1, y1, x2, y2) in enumerate(segs):
        if used[i]:
            continue
        used[i] = True
        loop = [(x1, y1), (x2, y2)]
        cur = (x2, y2)
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

def area(L):
    return sum(L[i][0] * L[(i + 1) % len(L)][1] - L[(i + 1) % len(L)][0] * L[i][1] for i in range(len(L))) / 2

print("=== front wall cross-section at y=1.0 (front wall spans y 0..2.25) ===")
segs, ax = slice_plane(T, 1, 1.0)
print("axes", ax, "segs", len(segs))
for L in sorted(chain2(segs), key=lambda l: -abs(area(l))):
    xs = [p[0] for p in L]; ys = [p[1] for p in L]
    if abs(area(L)) < 0.5:
        continue
    print(f"  loop bbox u[{min(xs):6.2f},{max(xs):6.2f}] v[{min(ys):6.2f},{max(ys):6.2f}]  "
          f"size {max(xs)-min(xs):6.2f}x{max(ys)-min(ys):6.2f}  area {abs(area(L)):9.1f}")

print("\n=== post presence vs z (loop 6.4x6.4 near x=7.25,y=7.25) ===")
for zi in range(0, 30):
    z = zi * 0.5
    ls = chain2(slice_plane(T, 2, z)[0])
    found = [L for L in ls if abs(area(L)) > 20 and
             abs((max(p[0] for p in L) - min(p[0] for p in L)) - 6.4) < 0.3]
    print(f"  z={z:4.1f}  loops={len(ls):3d}  post-like={len(found)}  maxA={max((abs(area(L)) for L in ls), default=0):8.1f}")
