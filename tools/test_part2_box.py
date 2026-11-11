from test_perfect_box import create_perfect_hollow_box
import numpy as np
from collections import defaultdict

facets2 = create_perfect_hollow_box(98.0, 36.0, 40.0, 2.0, 2.0)
edge_counts2 = defaultdict(int)
for v1, v2, v3 in facets2:
    edges = [tuple(sorted((v1, v2))), tuple(sorted((v2, v3))), tuple(sorted((v3, v1)))]
    for e in edges:
        edge_counts2[e] += 1

open_edges2 = [e for e, c in edge_counts2.items() if c != 2]
print("Part 2 Open or non-manifold edges (MUST BE 0):", len(open_edges2))

total_vol2 = 0.0
for v1, v2, v3 in facets2:
    va = np.array(v1, dtype=float)
    vb = np.array(v2, dtype=float)
    vc = np.array(v3, dtype=float)
    cross = np.cross(vb - va, vc - va)
    total_vol2 += np.dot(va, cross) / 6.0

print(f"Part 2 Solid volume: {total_vol2 / 1000.0:.2f} cm^3")
