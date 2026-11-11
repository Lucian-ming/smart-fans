import json, sys, requests, sexpdata
from pathlib import Path
from shapely.geometry import Point, box, LineString, Polygon
from shapely.ops import unary_union
from gerbonara import GerberFile
from gerbonara.graphic_objects import Flash,Line,Region
R=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(R/'tools'))
from verify_revb_copper import children,one,xy
p=sexpdata.loads((R/'hardware/kicad/fan_ctrl_revB.kicad_pcb').read_text(encoding='utf8'))
out={}; rings=[]; holes=[]
for fp in children(p,'footprint'):
 ref=next(str(n[2]) for n in children(fp,'property') if str(n[1])=='Reference')
 for pad in children(fp,'pad'):
  if children(pad,'drill'):
   w,h=xy(one(pad,'size')); d=float(one(pad,'drill')[1]); rings.append({'id':ref+'.'+str(pad[1]),'ring':(min(w,h)-d)/2,'drill':d})
for i,v in enumerate(children(p,'via')):rings.append({'id':'via'+str(i),'ring':(float(one(v,'size')[1])-float(one(v,'drill')[1]))/2,'drill':float(one(v,'drill')[1])})
out['rings_sorted']=sorted(rings,key=lambda x:x['ring']); out['min_drill']=min(x['drill'] for x in rings)
def geometry(o):
 if isinstance(o,Flash):
  a=o.aperture
  if hasattr(a,'diameter'): return Point(o.x,o.y).buffer(a.diameter/2,quad_segs=128)
  return box(o.x-a.w/2,o.y-a.h/2,o.x+a.w/2,o.y+a.h/2)
 if isinstance(o,Line): return LineString([(o.x1,o.y1),(o.x2,o.y2)]).buffer(o.aperture.diameter/2)
 if isinstance(o,Region): return Polygon(o.outline).buffer(0)
 raise Exception(type(o))
G=R/'hardware/fabrication/gerber_revB'
# outline radius from source is 3mm, centerline bounds 100..195
board=box(103,103,192,192).buffer(3,quad_segs=256)
for ext in ['GTL','GBL','GTS','GBS','GTO']:
 geoms=[geometry(o) for o in GerberFile.open(G/f'fan_ctrl_revB.{ext}').objects]
 u=unary_union(geoms)
 out[ext]={'objects':len(geoms),'edge_clearance':u.distance(board.boundary),'outside_area':u.difference(board).area}
 if ext in ['GTS','GBS']:
  pairs=[(a.distance(b),i,j,a.intersection(b).area) for i,a in enumerate(geoms) for j,b in enumerate(geoms[i+1:],i+1)]
  out[ext]['min_mask_gap']=min(pairs);out[ext]['pairs_under_0_1']=[x for x in pairs if x[0]<.1-1e-6]
 if ext=='GTS': mask=u
 if ext=='GTO':
  out[ext]['overlap_mask_area']=u.intersection(mask).area
  out[ext]['objects_on_mask']=sum(g.intersection(mask).area>1e-8 for g in geoms)
# exact upstream library files via GitHub API, not untrusted execution
for path in ['Package_TO_SOT_SMD.pretty/SOT-223-3_TabPin2.kicad_mod','Diode_SMD.pretty/D_SMA.kicad_mod','Diode_SMD.pretty/D_SOD-123.kicad_mod','Connector_BarrelJack.pretty/BarrelJack_Horizontal.kicad_mod']:
 url='https://api.github.com/repos/KiCad/kicad-footprints/contents/'+path
 resp=requests.get(url,timeout=25); row={'url':url,'status':resp.status_code}
 if resp.ok:
  import base64
  data=resp.json(); text=base64.b64decode(data['content']).decode(); target=R/'artifacts'/'footprint_reference'/Path(path).name; target.parent.mkdir(exist_ok=True);target.write_text(text,encoding='utf8')
  tree=sexpdata.loads(text);row['sha']=data['sha'];row['pads']=[str(n) for n in children(tree,'pad')];row['descr']=str(children(tree,'descr'))
 out[path]=row
pad_records=[]
for fp in children(p,'footprint'):
 fx,fy=xy(one(fp,'at'));ref=next(str(n[2]) for n in children(fp,'property') if str(n[1])=='Reference')
 for pad in children(fp,'pad'):
  x,y=xy(one(pad,'at'));pad_records.append({'id':ref+'.'+str(pad[1]),'xy':(fx+x,fy+y),'net':str(one(pad,'net')[2])})
for i,v in enumerate(children(p,'via')):pad_records.append({'id':'via'+str(i),'xy':xy(one(v,'at')),'net':int(one(v,'net')[1])})
for ext in ['GTS','GBS']:
 objects=GerberFile.open(G/f'fan_ctrl_revB.{ext}').objects
 out[ext]['pair_details']=[{'gap':gap,'a':min(pad_records,key=lambda r:Point(r['xy']).distance(Point(objects[i].x,objects[i].y))),'b':min(pad_records,key=lambda r:Point(r['xy']).distance(Point(objects[j].x,objects[j].y)))} for gap,i,j,area in out[ext]['pairs_under_0_1']]
out['min_pad_ring']=min(x['ring'] for x in rings if not x['id'].startswith('via'))
# Match silk-mask intersections to physical pad locations.
silk=unary_union([geometry(o) for o in GerberFile.open(G/'fan_ctrl_revB.GTO').objects])
maskobjects=GerberFile.open(G/'fan_ctrl_revB.GTS').objects
out['silk_on_mask_details']=[{'nearest':min(pad_records,key=lambda r:Point(r['xy']).distance(Point(o.x,o.y))),'area':silk.intersection(geometry(o)).area} for o in maskobjects if silk.intersection(geometry(o)).area>1e-8]
drills=[]
for fp in children(p,'footprint'):
 fx,fy=xy(one(fp,'at'));ref=next(str(n[2]) for n in children(fp,'property') if str(n[1])=='Reference')
 for pad in children(fp,'pad'):
  if children(pad,'drill'):
   x,y=xy(one(pad,'at'));drills.append((ref+'.'+str(pad[1]),fx+x,fy+y,float(one(pad,'drill')[1])))
for i,v in enumerate(children(p,'via')):
 x,y=xy(one(v,'at'));drills.append(('via'+str(i),x,y,float(one(v,'drill')[1])))
import math
webs=[{'a':a[0],'b':b[0],'hole_edge_gap':math.dist(a[1:3],b[1:3])-(a[3]+b[3])/2,'a_xy':a[1:3],'b_xy':b[1:3]} for i,a in enumerate(drills) for b in drills[i+1:]]
out['min_drill_web']=min(webs,key=lambda r:r['hole_edge_gap']);out['drill_web_under_025']=[r for r in webs if r['hole_edge_gap']<.25]
(R/'artifacts/pcb_release_footprint_metrics.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k!='rings_sorted'},indent=2));print('minimum rings',out['rings_sorted'][:5])
