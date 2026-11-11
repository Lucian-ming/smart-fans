import struct, math

def load(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    return [tuple(struct.unpack('<12f', d[84 + 50 * i:84 + 50 * i + 48])[3:12][j:j + 3] for j in (0, 3, 6))
            for i in range(n)]

T = load(r"D:/下载/SmartFan_Piece1_Base_Enclosure.stl")

def ray_y(x, z):
    """first hit along +Y at (x,z); returns y or None"""
    best = None
    for a, b, c in T:
        # project to (y,z)? ray dir = +Y, so solve in x,z plane
        # point on ray: (x, t, z); triangle plane
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        # solve (x,t,z) = a + s*u + r*v  in x,z components
        det = ux * vz - uz * vx
        if abs(det) < 1e-12:
            continue
        px, pz = x - a[0], z - a[2]
        s = (px * vz - pz * vx) / det
        r = (ux * pz - uz * px) / det
        if s < -1e-9 or r < -1e-9 or s + r > 1 + 1e-9:
            continue
        t = a[1] + s * uy + r * vy
        if best is None or t < best:
            best = t
    return best

print("front surface profile (min Y vs Z), sampled at x=48 and x=24")
for x in (48.0, 24.0, 72.0):
    print(f"\n x={x}")
    prev = None
    for zi in range(0, 57):
        z = zi * 0.5
        y = ray_y(x, z)
        if y is None:
            continue
        slope = ""
        if prev is not None and z > 0:
            dy = y - prev[1]; dz = z - prev[0]
            if abs(dz) > 1e-6:
                slope = f"  dy/dz={dy/dz:+.2f} ({math.degrees(math.atan2(dy,dz)):+.1f}deg from vertical)"
        print(f"   z={z:5.1f}  y_front={y:7.2f}{slope}")
        prev = (z, y)

print("\narea-weighted normal tilt histogram (2 deg bins)")
agg = {}
for a, b, c in T:
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    L = math.sqrt(sum(q * q for q in n))
    if L < 1e-9:
        continue
    nz = abs(n[2] / L)
    ang = math.degrees(math.acos(min(1, nz)))
    b_ = int(ang // 5) * 5
    agg[b_] = agg.get(b_, 0) + L / 2
for k in sorted(agg):
    print(f"   {k:3d}-{k+5:3d} deg : {agg[k]:9.1f} mm2")
