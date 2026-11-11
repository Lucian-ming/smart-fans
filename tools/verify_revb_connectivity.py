"""Connectivity and clearance audit helper, independent of route generator."""
from collections import defaultdict
from shapely.strtree import STRtree

def check_networks(pads, conductors, planes, clearance=0.25):
    nodes=list(conductors)
    for layer, geometry in planes.items():
        pieces=list(geometry.geoms) if hasattr(geometry,'geoms') else [geometry]
        for i,g in enumerate(pieces):
            nodes.append((f'plane_{layer}_{i}',1,layer,g))
    parent=list(range(len(nodes)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    def join(i,j):
        parent[find(i)]=find(j)
    # A via or plated through-hole is a physical inter-layer conductor.
    vertical=defaultdict(list)
    for i,n in enumerate(nodes):
        if n[0].startswith('via') or any(p['id']==n[0] and len(p['layers'])==2 for p in pads):
            vertical[n[0]].append(i)
    for ids in vertical.values():
        for i in ids[1:]:join(ids[0],i)
    clearance_errors=[]
    for layer in ['F.Cu','B.Cu']:
        ids=[i for i,n in enumerate(nodes) if n[2]==layer]
        geometries=[nodes[i][3] for i in ids];tree=STRtree(geometries)
        for local,i in enumerate(ids):
            a=nodes[i]
            for candidate in tree.query(a[3].buffer(clearance)):
                j=ids[int(candidate)]
                if j<=i:continue
                b=nodes[j];d=a[3].distance(b[3])
                if a[1]==b[1] and a[1]!=0:
                    if d<1e-6:join(i,j)
                elif d<clearance-1e-4:
                    # net-zero pads are intentionally NC but must not touch another net.
                    clearance_errors.append(dict(a=a[0],b=b[0],layer=layer,nets=[a[1],b[1]],distance_mm=round(d,6)))
    groups=defaultdict(lambda:defaultdict(set))
    pad_ids={p['id'] for p in pads if p['net']>0}
    for i,n in enumerate(nodes):
        if n[0] in pad_ids:groups[n[1]][find(i)].add(n[0])
    disconnected=[]
    for net,components in groups.items():
        if len(components)>1:disconnected.append(dict(net=net,pad_groups=[sorted(v) for v in components.values()]))
    return dict(clearance_mm=clearance,clearance_violation_count=len(clearance_errors),clearance_violations=clearance_errors,disconnected_net_count=len(disconnected),disconnected_nets=disconnected)
