import trimesh
from manifold3d import Manifold

def build_pure_monolithic_gimbal():
    # Pure monolithic 1-piece gimbal bracket for 12025 fan
    # Width: 98mm, Depth: 34mm, Height: 44mm
    # Base bottom saddle: thickness 5mm (Z=0 to 5)
    saddle_base = Manifold.cube([98.0, 34.0, 5.0], center=False)
    
    # Continuous upright side pillars: thickness 4.5mm each
    left_arm = Manifold.cube([4.5, 34.0, 44.0], center=False)
    right_arm = Manifold.cube([4.5, 34.0, 44.0], center=False).translate([93.5, 0.0, 0.0])
    
    # Front and rear fan retaining lips (4mm thick, 12mm high)
    front_lip = Manifold.cube([98.0, 3.5, 12.0], center=False).translate([0.0, 0.0, 5.0])
    back_lip = Manifold.cube([98.0, 3.5, 12.0], center=False).translate([0.0, 30.5, 5.0])
    
    gimbal = saddle_base + left_arm + right_arm + front_lip + back_lip
    
    # Central air flow window (reduces weight, allows smooth airflow)
    air_window = Manifold.cube([68.0, 24.0, 8.0], center=False).translate([15.0, 5.0, -1.0])
    gimbal = gimbal - air_window
    
    # Two M3 fan screw holes on the upright arms at Z=36 (pitch 105mm standard spacing)
    for hx in [2.25, 95.75]:
        fan_hole = Manifold.cylinder(38.0, 1.65, 1.65, circular_segments=20).rotate([90.0, 0, 0]).translate([hx, 36.0, 36.0])
        gimbal = gimbal - fan_hole
        
    # Bottom servo horn mounting boss and socket (centered at X=49.0, Y=17.0)
    # Boss D=16mm, H=6mm
    servo_boss = Manifold.cylinder(6.0, 8.0, 8.0, circular_segments=24).translate([49.0, 17.0, 0.0])
    # Recessed socket for MG90S factory servo horn (D=8.2mm, depth 4mm)
    servo_socket = Manifold.cylinder(5.0, 4.2, 4.2, circular_segments=24).translate([49.0, 17.0, -1.0])
    # Central screw pass-through hole (D=2.8mm)
    servo_screw = Manifold.cylinder(12.0, 1.4, 1.4, circular_segments=16).translate([49.0, 17.0, -2.0])
    
    gimbal = (gimbal + servo_boss) - servo_socket - servo_screw
    
    mesh = gimbal.to_mesh()
    tri_mesh = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts, process=True)
    
    print(f"Monolithic Gimbal:")
    print(f"  Watertight: {tri_mesh.is_watertight}")
    print(f"  Volume: {tri_mesh.volume / 1000.0:.2f} cm^3")
    print(f"  Bounds: {tri_mesh.bounding_box.extents}")
    print(f"  Facets: {len(tri_mesh.faces)}")
    return tri_mesh

build_pure_monolithic_gimbal()
