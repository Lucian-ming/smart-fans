import struct, numpy as np, sys

def load(p):
    d = open(p, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    V = []; F = []
    for i in range(n):
        v = struct.unpack('<12f', d[84 + 50 * i:84 + 50 * i + 48])
        V += [v[3:6], v[6:9], v[9:12]]
        F.append((3 * i, 3 * i + 1, 3 * i + 2))
    return np.array(V, float), np.array(F)

def weld(V, F):
    uq, inv = np.unique(np.round(V, 4), axis=0, return_inverse=True)
    return np.array(uq), inv[F]

STL = sys.argv[1] if len(sys.argv) > 1 else "mechanical/stl/print/SmartFan_Piece1_Base_Enclosure.stl"
V, F = load(STL)
V, F = weld(V, F)
tri = V[F]
a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
nrm = np.cross(b - a, c - a)
area = 0.5 * np.linalg.norm(nrm, axis=1)
unit = nrm / np.linalg.norm(nrm, axis=1)[:, None]

# 25 deg sloped faces
m = (np.abs(unit[:, 2]) > 0.85) & (np.abs(unit[:, 1]) > 0.35) & (np.abs(unit[:, 0]) < 0.05)
ang = np.degrees(np.arccos(np.clip(np.abs(unit[:, 2]), 0, 1)))
print("slope faces:", m.sum(), "areas", area[m].sum().round(1), "angles", np.unique(np.round(ang[m], 1)))

N = np.array([0, np.sin(np.radians(25)), np.cos(np.radians(25))])
s = V @ N
cen = tri[m].mean(1)
cs = cen @ N
print("slope face s values:", np.unique(np.round(cs, 1)))

# outer cluster = larger s
smax = cs.max()
outer = m.copy()
outer[m] = cs > smax - 1.0
print("outer slope faces:", outer.sum(), "area", area[outer].sum().round(1),
      "s=", np.round(np.unique(np.round(tri[outer].reshape(-1, 3) @ N, 1)), 2))

# plane origin: centroid of largest outer face
idx = np.where(outer)[0][np.argmax(area[outer])]
p0 = tri[idx].mean(0)
print("p0", p0.round(2), "s0", round(p0 @ N, 2))

u = np.array([0, np.cos(np.radians(25)), -np.sin(np.radians(25))])
vv = np.array([1.0, 0, 0])

# panel extent in (x, t)
Pts = tri[outer].reshape(-1, 3)
rel = Pts - p0
Xall = rel @ vv
Tall = rel @ u
print("panel x range", Xall.min().round(2), Xall.max().round(2),
      " t range", Tall.min().round(2), Tall.max().round(2))

step = 0.25
xs = np.arange(Xall.min() + step, Xall.max() - step, step)
ts = np.arange(Tall.min() + step, Tall.max() - step, step)
X, T = np.meshgrid(xs, ts, indexing='xy')
shape = X.shape
P = p0 + X.reshape(-1, 1) * vv + T.reshape(-1, 1) * u + N * 6.0
D = np.repeat(-N[None, :], len(P), axis=0)

e1 = tri[:, 1] - tri[:, 0]
e2 = tri[:, 2] - tri[:, 0]
nhit = np.zeros(len(P), int)
tmin = np.full(len(P), np.nan)
for s0 in range(0, len(P), 1500):
    p = P[s0:s0 + 1500]; dd = D[s0:s0 + 1500]
    pv = np.cross(dd[:, None, :], e2[None, :, :])
    det = np.einsum('tj,rtj->rt', e1, pv)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(det == 0, 1, det), 0)
    tv = p[:, None, :] - tri[None, :, 0]
    uu = np.einsum('rtj,rtj->rt', tv, pv) * inv
    qv = np.cross(tv, e1[None, :, :])
    s2 = np.einsum('rj,rtj->rt', dd, qv) * inv
    t = np.einsum('tj,rtj->rt', e2, qv) * inv
    hit = ok & (uu >= -1e-6) & (s2 >= -1e-6) & (uu + s2 <= 1 + 1e-6) & (t > 1e-6)
    cnt = hit.sum(1)
    nhit[s0:s0 + 1500] = cnt
    tm = np.where(hit, t, np.inf).min(1)
    tmin[s0:s0 + 1500] = np.where(cnt > 0, tm, np.nan)

NH = nhit.reshape(shape)
TM = tmin.reshape(shape)
hole = (~np.isfinite(TM)) | (TM > 8.5)   # 2.2mm wall sits at t~6..8.2
print("cells:", NH.size, " hole cells:", hole.sum(), " (", round(hole.mean() * 100, 1), "% )")

# flood fill
lab = np.zeros(shape, int)
cur = 0
from collections import deque
for i in range(shape[0]):
    for j in range(shape[1]):
        if hole[i, j] and lab[i, j] == 0:
            cur += 1
            q = deque([(i, j)]); lab[i, j] = cur
            while q:
                y, x = q.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < shape[0] and 0 <= xx < shape[1] and hole[yy, xx] and lab[yy, xx] == 0:
                        lab[yy, xx] = cur; q.append((yy, xx))

print("\n=== 开孔分量 ===")
res = []
for k in range(1, cur + 1):
    ys, xs_ = np.where(lab == k)
    if len(ys) < 12:
        continue
    x0, x1 = xs[xs_].min(), xs[xs_].max()
    t0, t1 = ts[ys.min()], ts[ys.max()]
    A = len(ys) * step * step
    res.append((x0, x1, t0, t1, A, len(ys)))
res.sort(key=lambda r: r[0])
for r in res:
    print(f"  x {r[0]:6.2f}..{r[1]:6.2f} (w={r[1]-r[0]:5.2f})  t {r[2]:6.2f}..{r[3]:6.2f} (h={r[3]-r[2]:5.2f})  area={r[4]:7.1f}mm2  cells={r[5]}")

# save image
img = np.zeros(shape + (3,), np.uint8)
img[~hole] = (70, 70, 70)
img[hole] = (250, 250, 250)
from PIL import Image
Image.fromarray(img).save("tools/B4_panel.png")
print("saved tools/B4_panel.png")
print("wall check: min gap between components (in-plane mm):")
for i in range(len(res)):
    for j in range(i + 1, len(res)):
        dx = max(0, max(res[i][0] - res[j][1], res[j][0] - res[i][1]))
        dt = max(0, max(res[i][2] - res[j][3], res[j][2] - res[i][3]))
        d = (dx ** 2 + dt ** 2) ** 0.5
        print(f"   {i}->{j}: {d:.2f} mm  (dx={dx:.2f}, dt={dt:.2f})")
