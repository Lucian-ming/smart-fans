import trimesh
print("trimesh version:", trimesh.__version__)
# Test creating a box
box = trimesh.creation.box(extents=(95.0, 95.0, 26.0))
print("Box is watertight:", box.is_watertight)
print("Box volume:", box.volume / 1000.0, "cm^3")
