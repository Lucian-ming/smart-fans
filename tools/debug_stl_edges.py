import struct
from collections import defaultdict

def check_manifold_edges(path):
    with open(path, 'rb') as f:
        header = f.read(80)
        count = struct.unpack('<I', f.read(4))[0]
        facets = []
        for _ in range(count):
            data = struct.unpack('<12fH', f.read(50))
            v1 = (round(data[3], 3), round(data[4], 3), round(data[5], 3))
            v2 = (round(data[6], 3), round(data[7], 3), round(data[8], 3))
            v3 = (round(data[9], 3), round(data[10], 3), round(data[11], 3))
            facets.append((v1, v2, v3))
            
    print(f"\nChecking {path}: {len(facets)} triangles")
    
    # Map each undirected edge to count of triangles
    edge_counts = defaultdict(int)
    directed_edges = defaultdict(int)
    
    for v1, v2, v3 in facets:
        edges = [(v1, v2), (v2, v3), (v3, v1)]
        for va, vb in edges:
            directed_edges[(va, vb)] += 1
            undir = tuple(sorted((va, vb)))
            edge_counts[undir] += 1
            
    open_edges = [e for e, cnt in edge_counts.items() if cnt == 1]
    non_manifold_edges = [e for e, cnt in edge_counts.items() if cnt > 2]
    manifold_ok = [e for e, cnt in edge_counts.items() if cnt == 2]
    
    print(f"  Total unique edges: {len(edge_counts)}")
    print(f"  Proper 2-manifold edges (shared by exactly 2): {len(manifold_ok)}")
    print(f"  Open boundary edges (shared by 1 triangle): {len(open_edges)}")
    print(f"  Non-manifold edges (shared by >2 triangles): {len(non_manifold_edges)}")
    
    if open_edges:
        print("  Sample open edges (坏边 / 漏洞):")
        for e in open_edges[:10]:
            print("   ", e)
            
    if non_manifold_edges:
        print("  Sample non-manifold edges:")
        for e in non_manifold_edges[:10]:
            print("   ", e)

check_manifold_edges("D:/smart_fans/mechanical/stl/print/Part1_Base_Assembly_Kit_100mm.stl")
check_manifold_edges("D:/smart_fans/mechanical/stl/print/Part2_Fan_Gimbal_Kit_100mm.stl")
