"""Independent geometry audit of serialized PCB copper, not generator parameters."""
import json, math
from pathlib import Path
import sexpdata
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from strict_copper_geometry import strict_polygon, checked_main

ROOT = Path(__file__).resolve().parents[1]
def children(n, name):
    return [x for x in n if isinstance(x, list) and x and str(x[0]) == name]
def one(n, name):
    return children(n, name)[0]
def xy(n):
    return tuple(map(float, n[1:3]))
def audit(pcb_path=None, report_path=None):
    root = sexpdata.loads(Path(pcb_path or ROOT/'hardware/kicad/fan_ctrl_revB.kicad_pcb').read_text(encoding='utf-8'))
    pads=[]; conductors=[]; planes={}
    for fp in children(root,'footprint'):
        fx,fy=xy(one(fp,'at'))
        ref=next(str(x[2]) for x in children(fp,'property') if str(x[1])=='Reference')
        for p in children(fp,'pad'):
            px,py=xy(one(p,'at')); x,y=fx+px,fy+py
            w,h=xy(one(p,'size')); shape=str(p[3]); net=int(one(p,'net')[1])
            if shape=='circle': geom=Point(x,y).buffer(w/2,quad_segs=256)
            elif shape=='rect': geom=box(x-w/2,y-h/2,x+w/2,y+h/2)
            else: raise ValueError('Unsupported pad shape '+shape)
            layers=['F.Cu','B.Cu'] if str(p[2])=='thru_hole' else ['F.Cu']
            rec=dict(id=f'{ref}.{p[1]}',x=x,y=y,w=w,h=h,net=net,layers=layers,geom=geom)
            pads.append(rec)
            for layer in layers: conductors.append((rec['id'],net,layer,geom))
    for i,s in enumerate(children(root,'segment')):
        g=LineString([xy(one(s,'start')),xy(one(s,'end'))]).buffer(float(one(s,'width')[1])/2,quad_segs=32)
        conductors.append((f'track{i}',int(one(s,'net')[1]),str(one(s,'layer')[1]),g))
    for i,v in enumerate(children(root,'via')):
        g=Point(xy(one(v,'at'))).buffer(float(one(v,'size')[1])/2,quad_segs=64)
        for layer in ['F.Cu','B.Cu']: conductors.append((f'via{i}',int(one(v,'net')[1]),layer,g))
    for z in children(root,'zone'):
        if int(one(z,'net')[1])!=1: continue
        poly=unary_union([strict_polygon([xy(a) for a in children(one(f,'pts'),'xy')], source=f"PCB {one(z,'layer')[1]} filled_polygon[{i}]", require_ccw=True) for i,f in enumerate(children(z,'filled_polygon'))])
        planes[str(one(z,'layer')[1])]=poly
    rows=[]
    for p in pads:
        if p['net']==1: continue
        for layer in p['layers']:
            plane=planes[layer]; x,y=p['x'],p['y']
            axes={}
            for axis,ends in [('x',[(x-300,y),(x+300,y)]),('y',[(x,y-300),(x,y+300)])]:
                cross=plane.intersection(LineString(ends))
                half=p['w']/2 if axis=='x' else p['h']/2
                gap=Point(x,y).distance(cross)-half if not cross.is_empty else 999.
                axes[axis]=round(gap,6)
            distance=p['geom'].distance(plane)
            overlap=p['geom'].intersection(plane).area
            rows.append(dict(pad=p['id'],layer=layer,x_gap_mm=axes['x'],y_gap_mm=axes['y'],distance_mm=round(distance,6),overlap_mm2=overlap))
    collisions=[]
    for i,a in enumerate(conductors):
        for b in conductors[i+1:]:
            if a[1]==b[1] or a[2]!=b[2] or a[1]==0 or b[1]==0: continue
            if a[3].intersects(b[3]):
                collisions.append(dict(a=a[0],b=b[0],nets=[a[1],b[1]],layer=a[2],overlap_mm2=a[3].intersection(b[3]).area))
    failures=[r for r in rows if min(r['x_gap_mm'],r['y_gap_mm'],r['distance_mm'])<0.25-0.0001 or r['overlap_mm2']>1e-8]
    result=dict(non_ground_pads=sum(p['net']!=1 for p in pads),pad_layer_checks=len(rows),min_x_mm=min(r['x_gap_mm'] for r in rows),min_y_mm=min(r['y_gap_mm'] for r in rows),min_euclidean_mm=min(r['distance_mm'] for r in rows),zone_short_pad_count=len({r['pad'] for r in rows if r['overlap_mm2']>1e-8}),zone_failures=failures,all_checks=rows,other_copper_collision_count=len(collisions),other_copper_collisions=collisions)
    from verify_revb_connectivity import check_networks
    result.update(check_networks(pads, conductors, planes))
    explicit = check_networks(pads, conductors, {})
    result['explicit_route_disconnected_net_count'] = explicit['disconnected_net_count']
    result['explicit_route_disconnected_nets'] = explicit['disconnected_nets']
    out=Path(report_path or ROOT/'hardware/fabrication/validation/copper_audit.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['all_checks','other_copper_collisions','clearance_violations','disconnected_nets']},indent=2))
    return not failures and len(pads)>0 and not collisions and result['clearance_violation_count']==0 and result['disconnected_net_count']==0 and result['explicit_route_disconnected_net_count']==0
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--pcb',type=Path,default=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_pcb')
    ap.add_argument('--report',type=Path,default=ROOT/'hardware/fabrication/validation/copper_audit.json')
    args=ap.parse_args()
    raise SystemExit(checked_main(lambda: 0 if audit(args.pcb,args.report) else 1, args.report))
