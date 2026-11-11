import numpy as np

def quad_normal(p1, p2, p3, p4):
    v1 = np.array(p1, dtype=float)
    v2 = np.array(p2, dtype=float)
    v3 = np.array(p3, dtype=float)
    n = np.cross(v2 - v1, v3 - v1)
    return n / np.linalg.norm(n)

# Check correctly oriented inner facets:
w, d, h = 96.0, 96.0, 24.0
wall = 1.8
x0, x1 = wall, w - wall
y0, y1 = d - wall, wall # wait, y0 < y1

y0, y1 = wall, d - wall

# 1. Inner floor at z=wall: normal must be (0, 0, 1)
# quad: (x0, y0, wall), (x1, y0, wall), (x1, y1, wall), (x0, y1, wall)
n = quad_normal((x0, y0, wall), (x1, y0, wall), (x1, y1, wall), (x0, y1, wall))
print("Inner floor normal (want [0, 0, 1]):", n)

# 2. Inner front at y=y0: normal must be (0, 1, 0)
# quad: (x0, y0, wall), (x0, y0, h), (x1, y0, h), (x1, y0, wall)
n = quad_normal((x0, y0, wall), (x0, y0, h), (x1, y0, h), (x1, y0, wall))
print("Inner front normal (want [0, 1, 0]):", n)

# 3. Inner right at x=x1: normal must be (-1, 0, 0)
# quad: (x1, y0, wall), (x1, y0, h), (x1, y1, h), (x1, y1, wall)
n = quad_normal((x1, y0, wall), (x1, y0, h), (x1, y1, h), (x1, y1, wall))
print("Inner right normal (want [-1, 0, 0]):", n)

# 4. Inner back at y=y1: normal must be (0, -1, 0)
# quad: (x1, y1, wall), (x1, y1, h), (x0, y1, h), (x0, y1, wall)
n = quad_normal((x1, y1, wall), (x1, y1, h), (x0, y1, h), (x0, y1, wall))
print("Inner back normal (want [0, -1, 0]):", n)

# 5. Inner left at x=x0: normal must be (1, 0, 0)
# quad: (x0, y1, wall), (x0, y1, h), (x0, y0, h), (x0, y0, wall)
n = quad_normal((x0, y1, wall), (x0, y1, h), (x0, y0, h), (x0, y0, wall))
print("Inner left normal (want [1, 0, 0]):", n)
