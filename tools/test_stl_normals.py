import struct
import numpy as np

def quad_normal(p1, p2, p3, p4):
    # Two triangles: (p1, p2, p3) and (p1, p3, p4)
    # Normal is (p2 - p1) x (p3 - p1)
    v1 = np.array(p1)
    v2 = np.array(p2)
    v3 = np.array(p3)
    n = np.cross(v2 - v1, v3 - v1)
    return n

# Test inner cavity winding
# For outer box:
# Bottom face at z=0: outward normal is (0, 0, -1)
# Top face at z=h: outward normal is (0, 0, 1)
# Front face at y=0: outward normal is (0, -1, 0)
# Back face at y=d: outward normal is (0, 1, 0)
# Left face at x=0: outward normal is (-1, 0, 0)
# Right face at x=w: outward normal is (1, 0, 0)

# For inner cavity:
# Inner floor at z=wall: normal must point UP (+Z, into cavity) -> (0, 0, 1)
# Inner front at y=wall: normal must point BACK (+Y, into cavity) -> (0, 1, 0)
# Inner back at y=d-wall: normal must point FRONT (-Y, into cavity) -> (0, -1, 0)
# Inner left at x=wall: normal must point RIGHT (+X, into cavity) -> (1, 0, 0)
# Inner right at x=w-wall: normal must point LEFT (-X, into cavity) -> (-1, 0, 0)

print("Normal orientation rules established.")
