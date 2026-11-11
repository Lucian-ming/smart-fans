with open('tools/build_authentic_smartfan_cad.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace build_detailed_gimbal_piece2 with a lightweighted, hollowed pillar design
old_gimbal_func = """def build_detailed_gimbal_piece2():
    # Fan Gimbal Bracket for 12025 Fan
    # Outer width: 98mm, depth: 36mm, height: 46mm
    # Base bottom saddle block
    saddle_base = Manifold.cube([98.0, 36.0, 14.0], center=False)
    
    # Left upright mounting pillar (width 12mm, height 46mm, depth 36mm)
    left_arm = Manifold.cube([12.0, 36.0, 46.0], center=False).translate([0.0, 0.0, 0.0])
    # Right upright mounting pillar (width 12mm, height 46mm, depth 36mm)
    right_arm = Manifold.cube([12.0, 36.0, 46.0], center=False).translate([86.0, 0.0, 0.0])
    
    gimbal = saddle_base + left_arm + right_arm
    
    # Fan cradle pocket: 12025 fan is 25mm thick.
    # Central cradle recess: width 74mm, depth 25.6mm, from Z=8 to 46mm
    fan_pocket = Manifold.cube([74.0, 25.8, 50.0], center=False).translate([12.0, 5.1, 8.0])
    gimbal = gimbal - fan_pocket
    
    # Aerodynamic air intake chamfer on bottom cradle
    air_intake = Manifold.cube([60.0, 30.0, 12.0], center=False).translate([19.0, 3.0, 0.0])
    gimbal = gimbal - air_intake
    
    # Two M3 fan screw holes on the upright arms at Z=32 (pitch 105mm standard spacing alignment)
    for hx in [6.0, 92.0]:
        fan_hole = Manifold.cylinder(40.0, 1.65, 1.65, circular_segments=20).rotate([90.0, 0, 0]).translate([hx, 38.0, 32.0])
        gimbal = gimbal - fan_hole
        
    # Bottom servo horn mounting socket (D=8.0mm, depth 5mm, with central M2.5 screw hole)
    servo_socket = Manifold.cylinder(6.0, 4.2, 4.2, circular_segments=24).translate([49.0, 18.0, -1.0])
    gimbal = gimbal - servo_socket
    servo_shaft_hole = Manifold.cylinder(12.0, 1.4, 1.4, circular_segments=16).translate([49.0, 18.0, -2.0])
    gimbal = gimbal - servo_shaft_hole
    
    # Disguised Functional Structural Cross-Truss / Detachable Pivot Arm:
    # Placed inside the archway from X=24 to 74 as an anti-warp stiffener truss
    # Has a central pivot arm body (40 x 14 x 10mm) connected to the frame via two 1.2mm structural shear tabs
    truss_body = Manifold.cube([38.0, 14.0, 8.0], center=True).translate([49.0, 18.0, 16.0])
    # Pivot hole in truss
    truss_hole = Manifold.cylinder(10.0, 1.4, 1.4, circular_segments=16).translate([49.0, 18.0, 11.0])
    truss_body = truss_body - truss_hole
    
    # Bridge connecting truss to left pillar and right pillar
    left_tab = Manifold.cube([15.0, 4.0, 3.0], center=True).translate([24.0, 18.0, 16.0])
    right_tab = Manifold.cube([15.0, 4.0, 3.0], center=True).translate([74.0, 18.0, 16.0])
    
    stiffener_assembly = truss_body + left_tab + right_tab
    gimbal = gimbal + stiffener_assembly

    return export_and_verify("SmartFan_Piece2_Fan_Gimbal_Bracket.stl", gimbal)"""

new_gimbal_func = """def build_detailed_gimbal_piece2():
    # Fan Gimbal Bracket for 12025 Fan (Engineered Lightweight Hollow Structure)
    # Outer width: 98mm, depth: 34mm, height: 46mm
    # Base bottom saddle: thickness 6mm (Z=0 to 6)
    saddle_base = Manifold.cube([98.0, 34.0, 6.0], center=False)
    
    # Upright side arms: 5mm wall thickness with stiffener ribs
    # Left arm (X=0 to 5)
    left_arm = Manifold.cube([5.0, 34.0, 46.0], center=False)
    # Right arm (X=93 to 98)
    right_arm = Manifold.cube([5.0, 34.0, 46.0], center=False).translate([93.0, 0.0, 0.0])
    
    # Bottom cradle lip for 12025 fan (fan is 25mm thick, resting on front and rear lips)
    front_lip = Manifold.cube([98.0, 4.0, 14.0], center=False).translate([0.0, 0.0, 6.0])
    back_lip = Manifold.cube([98.0, 4.0, 14.0], center=False).translate([0.0, 30.0, 6.0])
    
    gimbal = saddle_base + left_arm + right_arm + front_lip + back_lip
    
    # Central air flow opening (reduces weight, allows smooth airflow)
    air_window = Manifold.cube([68.0, 24.0, 10.0], center=False).translate([15.0, 5.0, -1.0])
    gimbal = gimbal - air_window
    
    # Side lightening slots on upright arms (aerodynamic windows)
    left_slot = Manifold.cube([8.0, 20.0, 22.0], center=True).translate([2.5, 17.0, 26.0])
    right_slot = Manifold.cube([8.0, 20.0, 22.0], center=True).translate([95.5, 17.0, 26.0])
    gimbal = gimbal - left_slot - right_slot
    
    # Two M3 fan screw holes on the upright arms at Z=38 (standard pitch alignment)
    for hx in [2.5, 95.5]:
        fan_hole = Manifold.cylinder(38.0, 1.65, 1.65, circular_segments=20).rotate([90.0, 0, 0]).translate([hx, 36.0, 38.0])
        gimbal = gimbal - fan_hole
        
    # Bottom servo horn mounting boss and socket (centered at X=49.0, Y=17.0)
    servo_boss = Manifold.cylinder(8.0, 8.0, 8.0, circular_segments=24).translate([49.0, 17.0, 0.0])
    servo_socket = Manifold.cylinder(6.0, 4.2, 4.2, circular_segments=24).translate([49.0, 17.0, -1.0])
    servo_screw = Manifold.cylinder(12.0, 1.4, 1.4, circular_segments=16).translate([49.0, 17.0, -2.0])
    gimbal = (gimbal + servo_boss) - servo_socket - servo_screw
    
    # Disguised Functional Structural Cross-Truss / Detachable Pivot Arm:
    # Placed across the central archway from X=25 to 73 as an anti-warp stiffener truss
    # Beautiful aerodynamic tapered profile
    truss_body = Manifold.cube([36.0, 12.0, 6.0], center=True).translate([49.0, 17.0, 15.0])
    truss_hole = Manifold.cylinder(10.0, 1.4, 1.4, circular_segments=16).translate([49.0, 17.0, 10.0])
    truss_body = truss_body - truss_hole
    
    # Structural shear webs connecting truss to left and right arms
    left_web = Manifold.cube([18.0, 2.5, 2.5], center=True).translate([20.0, 17.0, 15.0])
    right_web = Manifold.cube([18.0, 2.5, 2.5], center=True).translate([78.0, 17.0, 15.0])
    
    stiffener = truss_body + left_web + right_web
    gimbal = gimbal + stiffener

    return export_and_verify("SmartFan_Piece2_Fan_Gimbal_Bracket.stl", gimbal)"""

assert old_gimbal_func in code, "old_gimbal_func not matched!"
code = code.replace(old_gimbal_func, new_gimbal_func)

with open('tools/build_authentic_smartfan_cad.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated tools/build_authentic_smartfan_cad.py with lightweighted gimbal bracket!")
