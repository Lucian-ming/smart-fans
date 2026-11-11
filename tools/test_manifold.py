import manifold3d
from manifold3d import Manifold, Mesh
import numpy as np

# Create a box
b1 = Manifold.cube([95.0, 95.0, 26.0], center=True)
# Hollow inner cavity
b2 = Manifold.cube([91.4, 91.4, 25.0], center=True).translate([0, 0, 1.8])
result = b1 - b2

mesh = result.to_mesh()
print("Result vertex count:", len(mesh.vert_properties))
print("Result tri count:", len(mesh.tri_verts))
print("Manifold volume:", result.volume() / 1000.0, "cm^3")
print("Status:", result.status())
