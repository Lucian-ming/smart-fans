import struct
import numpy as np

def analyze_stl(path):
    with open(path, 'rb') as f:
        header = f.read(80)
        count = struct.unpack('<I', f.read(4))[0]
        print(f"File: {path}, Facet count: {count}")
        
        # Read all facets
        facets = []
        for _ in range(count):
            data = struct.unpack('<12fH', f.read(50))
            n = data[0:3]
            v1 = data[3:6]
            v2 = data[6:9]
            v3 = data[9:12]
            facets.append((n, v1, v2, v3))
            
    # Calculate signed volume using divergence theorem
    # V = 1/6 * sum(v1 . (v2 x v3))
    total_vol = 0.0
    inverted_normals = 0
    for n, v1, v2, v3 in facets:
        v1 = np.array(v1)
        v2 = np.array(v2)
        v3 = np.array(v3)
        # computed normal by right-hand rule
        cross = np.cross(v2 - v1, v3 - v1)
        area2 = np.linalg.norm(cross)
        if area2 > 1e-9:
            comp_n = cross / area2
            dot = np.dot(n, comp_n)
            if dot < 0:
                inverted_normals += 1
        vol = np.dot(v1, cross) / 6.0
        total_vol += vol
        
    print(f"  Signed volume: {total_vol:.2f} mm^3 = {total_vol / 1000.0:.2f} cm^3")
    print(f"  Inverted normal facets: {inverted_normals} / {count}")

analyze_stl("D:/smart_fans/mechanical/stl/print/Part1_Base_Assembly_Kit_100mm.stl")
analyze_stl("D:/smart_fans/mechanical/stl/print/Part2_Fan_Gimbal_Kit_100mm.stl")
