"""Fail-closed polygon ingestion. Never repair/erase ambiguous serialized copper."""
import hashlib
import json
import math
from pathlib import Path
import sys
from shapely.geometry import Polygon
from shapely.validation import explain_validity

class AmbiguousCopperGeometry(ValueError):
    def __init__(self, detail):
        self.detail=detail
        super().__init__(json.dumps(detail,ensure_ascii=True))

def reject(reason,source,**details):
    raise AmbiguousCopperGeometry(dict(kind='unsupported_or_ambiguous_geometry',source=source,reason=reason,**details))

def strict_polygon(points,source='unspecified',require_ccw=False):
    pts=[tuple(map(float,p)) for p in points]
    if len(pts)<3 or any(len(p)!=2 or not all(map(math.isfinite,p)) for p in pts):
        reject('Non-finite or insufficient contour coordinates',source)
    edges=list(zip(pts,pts[1:]+pts[:1]))
    signed=math.fsum(a[0]*b[1]-b[0]*a[1] for a,b in edges)/2
    meta=dict(raw_signed_area_mm2=signed,vertex_count=len(pts),contour_sha256=hashlib.sha256(repr(pts).encode()).hexdigest())
    p=Polygon(pts)
    if not p.is_valid or not p.exterior.is_simple or p.is_empty or p.area<=1e-12:
        reject('Invalid/weakly-simple contour; fill semantics not inferred: '+explain_validity(p),source,**meta)
    if require_ccw and signed<=0:
        reject('Negative PCB fill contour requires explicit hole/winding semantics',source,**meta)
    return p

def require_dark(obj,source):
    if not getattr(obj,'polarity_dark',True):
        reject('Clear-polarity Gerber composition not implemented',source)

def gerber_polygon(points,source='Gerber contour'):
    """Ucamco 2019.06 4.12.1/4.12.3: simple contours and axial cut-ins only.
    Every contour is filled individually, independent of orientation. True crosses,
    diagonal/partial-overlap bridges, and unknown winding remain unsupported.
    """
    from collections import defaultdict
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union, polygonize_full
    from shapely.strtree import STRtree
    pts=[tuple(map(float,p)) for p in points]
    if len(pts)<3 or any(len(p)!=2 or not all(map(math.isfinite,p)) for p in pts):
        reject('Non-finite or insufficient contour',source)
    if pts[0]!=pts[-1]:pts.append(pts[0])
    edges=[(a,b) for a,b in zip(pts,pts[1:]) if a!=b]
    groups=defaultdict(list)
    for a,b in edges:groups[tuple(sorted((a,b)))].append((a,b))
    bridges=[];boundary=[];directions=set()
    for key,uses in groups.items():
        if len(uses)==1:boundary.append(key)
        elif len(uses)==2 and uses[0]==tuple(reversed(uses[1])):
            a,b=key
            if a[0]!=b[0] and a[1]!=b[1]:reject('Diagonal cut-in unsupported by Gerber 4.12.3',source)
            directions.add('V' if a[0]==b[0] else 'H');bridges.append(key)
        else:reject('Repeated edges are not exactly one reverse cut-in pair',source)
    if len(directions)>1:reject('Mixed cut-in directions',source)
    degree=defaultdict(int)
    for a,b in boundary:degree[a]+=1;degree[b]+=1
    if not degree or any(v!=2 for v in degree.values()):
        reject('Boundary after cut-in removal is not disjoint simple cycles',source)
    if any(a not in degree or b not in degree for a,b in bridges):
        reject('Cut-in does not join contour endpoints',source)
    keys=boundary+bridges;lines=[LineString(k) for k in keys];tree=STRtree(lines)
    for i,line in enumerate(lines):
        for j in tree.query(line):
            j=int(j)
            if j<=i:continue
            inter=line.intersection(lines[j])
            if inter.is_empty:continue
            shared=set(keys[i])&set(keys[j])
            if inter.geom_type!='Point' or tuple(inter.coords[0]) not in shared:
                reject('Crossing, partial overlap or non-endpoint touch',source)
    noded=unary_union(lines)
    faces,cuts,dangles,invalid=polygonize_full(noded)
    if not dangles.is_empty or not invalid.is_empty:
        reject('Polygonization contains unexplained dangling or invalid edges',source)
    if bridges:
        bridge_geom=unary_union([LineString(k) for k in bridges])
        if not cuts.difference(bridge_geom).is_empty or not bridge_geom.difference(cuts).is_empty:
            reject('Polygonization cuts differ from verified cut-in pairs',source)
    elif not cuts.is_empty:reject('Unexpected polygonization cuts',source)
    selected=[];signs=set()
    for face in faces.geoms:
        p=face.representative_point();x,y=p.x,p.y;crossings=0;winding=0
        # Classify against ORIGINAL unmodified directed segments, including bridges.
        for a,b in edges:
            if (a[1]>y)!=(b[1]>y):
                hit=a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
                if hit>x:
                    crossings+=1;winding+=1 if b[1]>a[1] else -1
        if abs(winding)>1:reject('Unsupported multiple winding in contour',source)
        if crossings%2:
            selected.append(face);signs.add(winding)
    if len(signs)>1:reject('Contour interior changes winding sign',source)
    if not selected:reject('Empty contour fill',source)
    result=unary_union(selected)
    if not result.is_valid:reject('Selected fill is invalid; no repair applied',source)
    return result

def strict_region(obj,source='Gerber region'):
    require_dark(obj,source)
    if any(c is not None for c in getattr(obj,'arc_centers',[])):
        reject('Region arcs require exact fill interpretation',source)
    return gerber_polygon(obj.outline,source)

def checked_main(call,default_report):
    try:
        result=call()
        return 0 if result is None else result
    except AmbiguousCopperGeometry as exc:
        path=Path(default_report)
        if '--report' in sys.argv:
            path=Path(sys.argv[sys.argv.index('--report')+1])
        for arg in sys.argv:
            if arg.startswith('--report='):path=Path(arg.split('=',1)[1])
        result=dict(passed=False,geometry_interpretation_pass=False,failures=['ambiguous_geometry'],errors=[exc.detail],note='No buffer(0), make_valid, or guessed winding repair was applied; this rejection is not by itself proof of an electrical short.')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=True,indent=2))
        return 1
