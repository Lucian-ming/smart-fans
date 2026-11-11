"""Independent manufacturing gate on final Gerbers/drill; includes same-net holes.
Exit 1 means a failed gate, not execution failure. No generator imports/mutations.
"""
import argparse,json,math,hashlib
from pathlib import Path
from collections import Counter
from gerbonara import GerberFile,ExcellonFile
from gerbonara.graphic_objects import Flash,Line,Region,Arc
from shapely.geometry import Point,box,LineString,Polygon
from shapely.ops import unary_union,polygonize
from strict_copper_geometry import strict_region, require_dark, checked_main
ROOT=Path(__file__).resolve().parents[1]
def geom(o,source='Gerber object'):
    require_dark(o,source)
    if isinstance(o,Flash):
        a=o.aperture
        if hasattr(a,'diameter'):return Point(o.x,o.y).buffer(a.diameter/2,quad_segs=256)
        if hasattr(a,'w') and hasattr(a,'h'):return box(o.x-a.w/2,o.y-a.h/2,o.x+a.w/2,o.y+a.h/2)
    if isinstance(o,Line):return LineString([(o.x1,o.y1),(o.x2,o.y2)]).buffer(o.aperture.diameter/2,quad_segs=32)
    if isinstance(o,Region):return strict_region(o,source)
    raise ValueError('Unsupported geometry: '+type(o).__name__)
def outline(g):
    segments=[]
    for o in g.objects:
        if isinstance(o,Arc):
            cx,cy=o.x1+o.cx,o.y1+o.cy
            r=math.hypot(o.cx,o.cy)
            a=math.atan2(o.y1-cy,o.x1-cx);b=math.atan2(o.y2-cy,o.x2-cx)
            sweep=-((a-b)%(2*math.pi)) if o.clockwise else (b-a)%(2*math.pi)
            n=max(32,math.ceil(abs(sweep)/.001))
            pts=[(cx+r*math.cos(a+sweep*i/n),cy+r*math.sin(a+sweep*i/n)) for i in range(n+1)]
            pts[0]=(o.x1,o.y1);pts[-1]=(o.x2,o.y2);segments.append(LineString(pts))
        elif isinstance(o,Line):segments.append(LineString([(o.x1,o.y1),(o.x2,o.y2)]))
        else:raise ValueError('Unsupported board outline object '+type(o).__name__)
    from shapely.ops import polygonize_full
    from strict_copper_geometry import reject
    noded=unary_union(segments)
    if abs(sum(s.length for s in segments)-noded.length)>1e-6:
        reject('Duplicate/overlapping board outline edges', 'GKO outline')
    polygons,cuts,dangles,invalid=polygonize_full(noded)
    if not cuts.is_empty or not dangles.is_empty or not invalid.is_empty:
        reject('Board contour polygonization has unused or invalid edges', 'GKO outline')
    polys=list(polygons.geoms)
    if len(polys)!=1:reject('Expected one unambiguous closed board contour', 'GKO outline',polygon_count=len(polys))
    return polys[0]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--gerbers',type=Path,default=ROOT/'hardware/fabrication/gerber_revB')
    ap.add_argument('--report',type=Path,default=ROOT/'hardware/fabrication/validation/manufacturing_audit.json')
    ap.add_argument('--copper-edge',type=float,default=.25)
    ap.add_argument('--drill-web',type=float,default=.25)
    ap.add_argument('--mask-bridge',type=float,default=.1)
    ap.add_argument('--silk-clearance',type=float,default=.1)
    args=ap.parse_args();G=args.gerbers
    files={ext:G/f'fan_ctrl_revB.{ext}' for ext in ['GKO','GTL','GBL','GTS','GBS','GTO','DRL']}
    result={'limits_mm':{'copper_edge':args.copper_edge,'drill_web':args.drill_web,'mask_bridge':args.mask_bridge,'silk_clearance':args.silk_clearance},'failures':[],'file_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files.values()},'notes':['Ideal geometry only, not drill registration/plating tolerance guarantee.','All drill pairs checked regardless of electrical net.','Merged same-net mask openings are reported as failed bridges pending explicit process waiver; not proof of an electrical short.','Gerber drill slots/arcs unsupported: fail closed rather than silently skip.','Board contour from actual GKO centerline, not stroke outer bounds.']}
    board=outline(GerberFile.open(files['GKO']))
    for ext in ['GTL','GBL']:
        objects=[geom(o,f'{ext} object[{i}]') for i,o in enumerate(GerberFile.open(files[ext]).objects)];u=unary_union(objects)
        edge=u.distance(board.boundary);outside=u.difference(board).area
        result[ext]={'min_board_edge_mm':edge,'outside_area_mm2':outside,'object_count':len(objects)}
        if edge<args.copper_edge-1e-5 or outside>1e-8:result['failures'].append(ext+'_copper_edge')
    drill=ExcellonFile.open(files['DRL']);holes=[]
    for i,o in enumerate(drill.objects):
        if not isinstance(o,Flash):raise ValueError('Drill slot needs exact slot support: '+type(o).__name__)
        holes.append({'index':i,'x':o.x,'y':o.y,'diameter':o.tool.diameter})
    pairs=[];minimum=None
    for i,a in enumerate(holes):
        for b in holes[i+1:]:
            gap=math.hypot(a['x']-b['x'],a['y']-b['y'])-(a['diameter']+b['diameter'])/2
            row={'a':a,'b':b,'edge_gap_mm':gap}
            if minimum is None or gap<minimum['edge_gap_mm']:minimum=row
            if gap<args.drill_web-1e-6:pairs.append(row)
    result['drill']={'hit_count':len(holes),'pair_count':len(holes)*(len(holes)-1)//2,'minimum':minimum,'violations':pairs}
    if pairs:result['failures'].append('drill_web')
    mask=None
    for ext in ['GTS','GBS']:
        obs=GerberFile.open(files[ext]).objects;gs=[geom(o) for o in obs];pairs=[];minimum=float('inf')
        for i,a in enumerate(gs):
            for j,b in enumerate(gs[i+1:],i+1):
                gap=a.distance(b);minimum=min(minimum,gap)
                if gap<args.mask_bridge-1e-6:pairs.append({'a_index':i,'b_index':j,'a_xy':[obs[i].x,obs[i].y],'b_xy':[obs[j].x,obs[j].y],'gap_mm':gap,'overlap_mm2':a.intersection(b).area})
        result[ext]={'opening_count':len(gs),'min_bridge_mm':minimum,'violations':pairs}
        if pairs:result['failures'].append(ext+'_mask_bridge')
        if ext=='GTS':mask=unary_union(gs)
    gs=[geom(o) for o in GerberFile.open(files['GTO']).objects];silk=unary_union(gs)
    overlap=silk.intersection(mask).area
    result['GTO']={'overlap_mask_mm2':overlap,'objects_on_mask':sum(g.intersection(mask).area>1e-8 for g in gs),'objects_within_clearance':sum(g.distance(mask)<args.silk_clearance-1e-6 for g in gs),'min_mask_distance_mm':silk.distance(mask)}
    if overlap>1e-8 or silk.distance(mask)<args.silk_clearance-1e-6:result['failures'].append('silk_mask_clearance')
    result['passed']=not result['failures'];args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed':result['passed'],'failures':result['failures'],'report':str(args.report),'drill_pairs_checked':result['drill']['pair_count'],'min_copper_edge_mm':min(result[e]['min_board_edge_mm'] for e in ['GTL','GBL']),'silk_mask_overlap_mm2':overlap},indent=2))
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(checked_main(main, ROOT/'hardware/fabrication/validation/manufacturing_audit.json'))
