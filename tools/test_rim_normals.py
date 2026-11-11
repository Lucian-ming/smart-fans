import numpy as np

def quad_normal(p1, p2, p3, p4):
    v1 = np.array(p1, dtype=float)
    v2 = np.array(p2, dtype=float)
    v3 = np.array(p3, dtype=float)
    n = np.cross(v2 - v1, v3 - v1)
    return n / np.linalg.norm(n)

w, d, h = 96.0, 96.0, 24.0
wall = 1.8
x0, x1 = wall, w - wall
y0, y1 = wall, d - wall

# Left rim: (0, 0, h), (x0, 0, h), (x0, d, h), (0, d, h)
print("Left rim:", quad_normal((0, 0, h), (x0, 0, h), (x0, d, h), (0, d, h)))
# Back rim: (0, d, h), (x0, d, h), (x1, d, h), (w, d, h)
# Right rim: (x1, 0, h), (w, 0, h), (w, d, h), (x1, d, h)
print("Right rim:", quad_normal((x1, 0, h), (w, 0, h), (w, d, h), (x1, d, h)))
# Front rim: (0, 0, h), (w, 0, h), (x1, y0, h), (x0, y0, h)
# Let's make all 4 rims neat non-overlapping:
# Left rim: x from 0 to x0, y from y0 to y1
# Right rim: x from x1 to w, y from y0 to y1
# Front rim: x from 0 to w, y from 0 to y0
# Back rim: x from 0 to w, y from y1 to d
print("Front rim:", quad_normal((0, 0, h), (w, 0, h), (w, y0, h), (0, y0, h)))
print("Back rim:", quad_normal((0, y1, h), (w, y1, h), (w, d, h), (0, d, h)))
print("Left rim:", quad_normal((0, y0, h), (x0, y0, h), (x0, y1, h), (0, y1, h)))
print("Right rim:", quad_normal((x1, y0, h), (w, y0, h), (w, y1, h), (x1, y1, h)))
