import numpy as np
from collections import defaultdict

def create_perfect_hollow_box(w, d, h, wall, t_floor):
    x0, x1 = wall, w - wall
    y0, y1 = wall, d - wall

    # 16 Vertices
    # Outer: O0..O7
    O0 = (0.0, 0.0, 0.0)
    O1 = (w, 0.0, 0.0)
    O2 = (w, d, 0.0)
    O3 = (0.0, d, 0.0)
    O4 = (0.0, 0.0, h)
    O5 = (w, 0.0, h)
    O6 = (w, d, h)
    O7 = (0.0, d, h)

    # Inner: I0..I7
    I0 = (x0, y0, t_floor)
    I1 = (x1, y0, t_floor)
    I2 = (x1, y1, t_floor)
    I3 = (x0, y1, t_floor)
    I4 = (x0, y0, h)
    I5 = (x1, y0, h)
    I6 = (x1, y1, h)
    I7 = (x0, y1, h)

    facets = []
    def add_quad(p1, p2, p3, p4):
        # Adds 2 triangles CCW when looking from outside solid
        facets.append((p1, p2, p3))
        facets.append((p1, p3, p4))

    # 1. Outer Bottom (z=0, normal [0, 0, -1])
    add_quad(O0, O3, O2, O1)

    # 2. Outer Sides (normals pointing outward)
    add_quad(O0, O1, O5, O4) # Front (normal [0, -1, 0])
    add_quad(O1, O2, O6, O5) # Right (normal [1, 0, 0])
    add_quad(O2, O3, O7, O6) # Back (normal [0, 1, 0])
    add_quad(O3, O0, O4, O7) # Left (normal [-1, 0, 0])

    # 3. Top Rim (z=h, normal [0, 0, 1])
    add_quad(O4, O5, I5, I4) # Front rim
    add_quad(O5, O6, I6, I5) # Right rim
    add_quad(O6, O7, I7, I6) # Back rim
    add_quad(O7, O4, I4, I7) # Left rim

    # 4. Inner Sides (normals pointing into cavity)
    add_quad(I4, I5, I1, I0) # Front inner (normal [0, 1, 0])
    add_quad(I5, I6, I2, I1) # Right inner (normal [-1, 0, 0])
    add_quad(I6, I7, I3, I2) # Back inner (normal [0, -1, 0])
    add_quad(I7, I4, I0, I3) # Left inner (normal [1, 0, 0])

    # 5. Inner Floor (z=t_floor, normal [0, 0, 1])
    add_quad(I0, I1, I2, I3)

    return facets

facets = create_perfect_hollow_box(96.0, 96.0, 24.0, 1.8, 1.8)
print(f"Generated {len(facets)} triangles.")

# Check topology
edge_counts = defaultdict(int)
for v1, v2, v3 in facets:
    edges = [tuple(sorted((v1, v2))), tuple(sorted((v2, v3))), tuple(sorted((v3, v1)))]
    for e in edges:
        edge_counts[e] += 1

open_edges = [e for e, c in edge_counts.items() if c != 2]
print("Open or non-manifold edges (MUST BE 0):", len(open_edges))

# Calculate volume
total_vol = 0.0
for v1, v2, v3 in facets:
    va = np.array(v1, dtype=float)
    vb = np.array(v2, dtype=float)
    vc = np.array(v3, dtype=float)
    cross = np.cross(vb - va, vc - va)
    total_vol += np.dot(va, cross) / 6.0

print(f"Calculated solid volume: {total_vol / 1000.0:.2f} cm^3")
