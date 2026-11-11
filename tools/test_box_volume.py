import numpy as np

def test_box_volume():
    w, d, h = 96.0, 96.0, 24.0
    wall = 1.8
    x0, x1 = wall, w - wall
    y0, y1 = wall, d - wall

    facets = []
    def quad(p1, p2, p3, p4):
        facets.append((p1, p2, p3))
        facets.append((p1, p3, p4))

    # Outer 6 faces (bottom at z=0, 4 sides)
    # Bottom: (0, 0, 0), (0, d, 0), (w, d, 0), (w, 0, 0) -> normal [0, 0, -1]
    quad((0, 0, 0), (0, d, 0), (w, d, 0), (w, 0, 0))
    # Front outer (y=0): (0, 0, 0), (w, 0, 0), (w, 0, h), (0, 0, h) -> normal [0, -1, 0]
    quad((0, 0, 0), (w, 0, 0), (w, 0, h), (0, 0, h))
    # Right outer (x=w): (w, 0, 0), (w, d, 0), (w, d, h), (w, 0, h) -> normal [1, 0, 0]
    quad((w, 0, 0), (w, d, 0), (w, d, h), (w, 0, h))
    # Back outer (y=d): (w, d, 0), (0, d, 0), (0, d, h), (w, d, h) -> normal [0, 1, 0]
    quad((w, d, 0), (0, d, 0), (0, d, h), (w, d, h))
    # Left outer (x=0): (0, d, 0), (0, 0, 0), (0, 0, h), (0, d, h) -> normal [-1, 0, 0]
    quad((0, d, 0), (0, 0, 0), (0, 0, h), (0, d, h))

    # 4 Top Rims (z=h) -> normal [0, 0, 1]
    quad((0, 0, h), (w, 0, h), (w, y0, h), (0, y0, h)) # Front rim
    quad((0, y1, h), (w, y1, h), (w, d, h), (0, d, h)) # Back rim
    quad((0, y0, h), (x0, y0, h), (x0, y1, h), (0, y1, h)) # Left rim
    quad((x1, y0, h), (w, y0, h), (w, y1, h), (x1, y1, h)) # Right rim

    # Inner cavity (floor at z=wall, 4 inner walls)
    # Inner floor: (x0, y0, wall), (x1, y0, wall), (x1, y1, wall), (x0, y1, wall) -> normal [0, 0, 1]
    quad((x0, y0, wall), (x1, y0, wall), (x1, y1, wall), (x0, y1, wall))
    # Inner front (y=y0): normal [0, 1, 0]
    quad((x0, y0, wall), (x0, y0, h), (x1, y0, h), (x1, y0, wall))
    # Inner right (x=x1): normal [-1, 0, 0]
    quad((x1, y0, wall), (x1, y0, h), (x1, y1, h), (x1, y1, wall))
    # Inner back (y=y1): normal [0, -1, 0]
    quad((x1, y1, wall), (x1, y1, h), (x0, y1, h), (x0, y1, wall))
    # Inner left (x=x0): normal [1, 0, 0]
    quad((x0, y1, wall), (x0, y1, h), (x0, y0, h), (x0, y0, wall))

    # Compute signed volume
    total_vol = 0.0
    for v1, v2, v3 in facets:
        v1 = np.array(v1, dtype=float)
        v2 = np.array(v2, dtype=float)
        v3 = np.array(v3, dtype=float)
        cross = np.cross(v2 - v1, v3 - v1)
        total_vol += np.dot(v1, cross) / 6.0

    print(f"Total facets: {len(facets)}")
    print(f"Calculated signed volume: {total_vol:.2f} mm^3 = {total_vol / 1000.0:.2f} cm^3")

test_box_volume()
