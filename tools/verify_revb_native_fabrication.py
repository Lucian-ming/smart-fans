"""Fail-closed native Gerber manufacturing audit. No repair, fitting or CAD execution.
Coordinate contract: KiCad absolute (x,y) -> Gerber absolute (x,-y), zero plot offset.
Only explicitly implemented geometry is accepted. Thresholds are design gates, not fab certification.
"""
import argparse, hashlib, json, math, traceback
from collections import Counter
from pathlib import Path
from gerbonara import GerberFile, ExcellonFile
from gerbonara.graphic_objects import Flash, Line, Arc, Region
from gerbonara.apertures import CircleAperture, RectangleAperture
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely.affinity import rotate, translate
from validate_revB_schematic import parse, one, children, xy
from strict_copper_geometry import strict_region, require_dark
from verify_revb_manufacturing import outline

TOL=0.003  # mm, conservative polygon/export quantization allowance

def number(n,key,default=0):
 a=children(n,key);return float(a[0][1]) if a else default

def coord(n):
 x,y=xy(n);return x,-y

def net(n,net_names):
 a=children(n,'net')
 if not a:return 'NC'
 values=a[0][1:]
 if len(values)==2:
  code,name=values
  if int(code) in net_names and net_names[int(code)]!=str(name):raise ValueError('Inconsistent net code/name')
  return str(name) or 'NC'
 if len(values)!=1:raise ValueError('Unsupported net serialization '+str(a))
 value=values[0]
 if isinstance(value,(int,float)) or (net_names and str(value).lstrip('-').isdigit()):
  if int(value)==0:return 'NC'
  if int(value) not in net_names:raise ValueError('Unmapped numeric net '+str(value))
  return net_names[int(value)]
 return str(value) or 'NC'

def shape(kind,w,h):
 if kind=='circle' and abs(w-h)<1e-8:return Point(0,0).buffer(w/2,quad_segs=256)
 if kind=='rect':return box(-w/2,-h/2,w/2,h/2)
 raise ValueError('Unsupported pad/aperture geometry '+str((kind,w,h)))

def object_geom(o,source):
 require_dark(o,source)
 if isinstance(o,Region):return strict_region(o,source)
 if isinstance(o,Flash):
  a=o.aperture
  if isinstance(a,CircleAperture):g=shape('circle',a.diameter,a.diameter)
  elif isinstance(a,RectangleAperture):g=shape('rect',a.w,a.h)
  else:raise ValueError('Unsupported flash aperture '+type(a).__name__)
  if getattr(a,'hole_dia',None):raise ValueError('Aperture hole unsupported')
  return translate(g,o.x,o.y)
 if isinstance(o,Line) and isinstance(o.aperture,CircleAperture):
  return LineString([(o.x1,o.y1),(o.x2,o.y2)]).buffer(o.aperture.diameter/2,quad_segs=64)
 raise ValueError('Unsupported Gerber object '+type(o).__name__)

def linekey(a,b,w):return (*sorted([tuple(round(v,5) for v in a),tuple(round(v,5) for v in b)]),round(w,5))
def drillkey(x,y,d):return round(x,3),round(y,3),round(d,3)
def component_deviation(a,b):
 aa=list(a.geoms) if hasattr(a,'geoms') else [a];bb=list(b.geoms) if hasattr(b,'geoms') else [b]
 if len(aa)!=len(bb):return None
 unused=set(range(len(bb)));worst=0.0
 for g in aa:
  matches=[i for i in unused if all(abs(x-y)<=.02 for x,y in zip(g.bounds,bb[i].bounds))]
  if len(matches)!=1:return None
  i=matches[0];worst=max(worst,g.hausdorff_distance(bb[i]));unused.remove(i)
 return worst

def same_geometry(a,b):
 if a.is_empty or b.is_empty:return a.is_empty and b.is_empty
 deviation=component_deviation(a,b)
 return deviation is not None and deviation<=TOL and a.symmetric_difference(b).area<=max(.003,a.length*TOL)

def audit(pcb_path,directory):
 pcb=parse(pcb_path.read_text(encoding='utf8'));errors=[];metrics={}
 net_names={int(v[1]):str(v[2]) for v in children(pcb,'net') if len(v)==3}
 resolve_net=lambda n:net(n,net_names)
 def fail(kind,**kw):errors.append(dict(kind=kind,**kw))
 files={}
 for layer,suffix in [('F.Cu','gtl'),('B.Cu','gbl'),('F.Paste','gtp'),('B.Paste','gbp'),('F.Mask','gts'),('B.Mask','gbs'),('F.SilkS','gto'),('B.SilkS','gbo'),('Edge.Cuts','gm1')]:
  hits=list(directory.glob('*.'+suffix))
  if len(hits)!=1:raise ValueError('Expected exactly one '+suffix+' file: '+str(hits))
  files[layer]=hits[0]
 drills={}
 for plating in ['PTH','NPTH']:
  hits=[p for p in directory.glob('*.drl') if p.stem.endswith('-'+plating)]
  if len(hits)!=1:raise ValueError('Expected one '+plating+' drill file')
  drills[plating]=hits[0]
 parsed={};geoms={}
 # Parse EVERY layer before any acceptance; even an empty back silk is inspected.
 for layer,path in files.items():
  g=GerberFile.open(path);parsed[layer]=g
  if str(g.unit)!='mm':raise ValueError('Unsupported Gerber unit '+str(g.unit))
  for i,o in enumerate(g.objects):require_dark(o,f'{path.name}[{i}]')
  if layer!='Edge.Cuts':geoms[layer]=[object_geom(o,f'{path.name}[{i}]') for i,o in enumerate(g.objects)]
 board=outline(parsed['Edge.Cuts']);metrics['board_bounds_gerber']=list(board.bounds)
 # Verify serialized board edge endpoints; no translation/mirror fit is permitted.
 expected_edges=[]
 for kind in ['gr_line','gr_arc']:
  for e in children(pcb,kind):
   if one(e,'layer')[1]!='Edge.Cuts':continue
   expected_edges.extend([coord(one(e,'start')),coord(one(e,'end'))])
 got_edges=[p for o in parsed['Edge.Cuts'].objects for p in [(o.x1,o.y1),(o.x2,o.y2)]]
 if Counter(tuple(round(v,5) for v in p) for p in expected_edges)!=Counter(tuple(round(v,5) for v in p) for p in got_edges):fail('board_edge_endpoint_mismatch')
 # Absolute transforms are explicit, including footprint rotation in KiCad Y-down.
 pads=[];mask_owners={'F.Mask':[],'B.Mask':[]};copper_by_layer={};expected_holes={'PTH':[],'NPTH':[]};sources={'F.Cu':[],'B.Cu':[]};expected_masks={'F.Mask':[],'B.Mask':[]};expected_paste={'F.Paste':[],'B.Paste':[]}
 margin=number(one(pcb,'setup'),'pad_to_mask_clearance',0)
 for fp in children(pcb,'footprint'):
  at=one(fp,'at');fx,fy=xy(at);fa=float(at[3]) if len(at)>3 else 0
  ref=next((v[2] for v in children(fp,'property') if v[1]=='Reference'),'?')
  for p in children(fp,'pad'):
   pa=one(p,'at');px,py=xy(pa);ang=float(pa[3]) if len(pa)>3 else fa
   # KiCad footprint rotation is CCW in physical Y-up space.
   t=math.radians(fa);x=fx+px*math.cos(t)+py*math.sin(t);y=-(fy-px*math.sin(t)+py*math.cos(t))
   w,h=xy(one(p,'size'));kind=str(p[3]);g=translate(rotate(shape(kind,w,h),ang,origin=(0,0)),x,y)
   layers=one(p,'layers')[1:];row=dict(ref=ref,pin=p[1],net=resolve_net(p),geom=g,x=x,y=y,layers=layers);pads.append(row)
   for layer in sources:
    if layer in layers or '*.Cu' in layers:sources[layer].append((resolve_net(p),g,ref+'.'+p[1]))
   for layer in expected_masks:
    if layer in layers or '*.Mask' in layers:
     m=number(p,'solder_mask_margin',number(fp,'solder_mask_margin',margin))
     opening=shape(kind,w,h)
     if m!=0:opening=opening.buffer(m,quad_segs=256)
     expected_masks[layer].append(translate(rotate(opening,ang,origin=(0,0)),x,y))
     mask_owners[layer].append((resolve_net(p),ref+'.'+p[1],expected_masks[layer][-1]))
   for layer in expected_paste:
    if layer in layers:
     m=number(p,'solder_paste_margin',number(fp,'solder_paste_margin',number(one(pcb,'setup'),'pad_to_paste_clearance',0)))
     ratio=number(p,'solder_paste_margin_ratio',number(fp,'solder_paste_margin_ratio',number(one(pcb,'setup'),'pad_to_paste_clearance_ratio',0)))
     expected_paste[layer].append(translate(rotate(shape(kind,w+2*m+2*w*ratio,h+2*m+2*h*ratio),ang,origin=(0,0)),x,y))
   ds=children(p,'drill')
   if ds:
    if len(ds[0])!=2:raise ValueError('Slot/offset drill unsupported: '+ref+'.'+p[1])
    d=float(ds[0][1]);plating='NPTH' if p[2]=='np_thru_hole' else 'PTH'
    expected_holes[plating].append(dict(x=x,y=y,d=d,net=resolve_net(p),owner=ref+'.'+p[1],geom=Point(x,y).buffer(d/2,quad_segs=256)))
 for v in children(pcb,'via'):
  x,y=coord(one(v,'at'));d=number(v,'drill');w=number(v,'size');g=Point(x,y).buffer(w/2,quad_segs=256)
  for layer in sources:sources[layer].append((resolve_net(v),g,'via'))
  expected_holes['PTH'].append(dict(x=x,y=y,d=d,net=resolve_net(v),owner='via',geom=Point(x,y).buffer(d/2,quad_segs=256)))
 for t in children(pcb,'segment'):
  layer=one(t,'layer')[1];g=LineString([coord(one(t,'start')),coord(one(t,'end'))]).buffer(number(t,'width')/2,quad_segs=64)
  sources[layer].append((resolve_net(t),g,'track'))
 # Native plane Regions are assigned only if this PCB has one unique zone net per layer.
 for layer in sources:
  zones=[z for z in children(pcb,'zone') if children(z,'layer') and one(z,'layer')[1]==layer]
  zn={resolve_net(z) for z in zones}
  if len(zn)!=1:raise ValueError('Expected one zone net per layer, got '+str(zn))
  regions=[g for o,g in zip(parsed[layer].objects,geoms[layer]) if isinstance(o,Region)]
  zone=unary_union(regions);znet=next(iter(zn))
  if zone.is_empty:fail('missing_plane',layer=layer)
  nonplane=[(n,g,name) for n,g,name in sources[layer] if n!=znet]
  violations=[]
  for n,g,name in nonplane:
   distance=zone.distance(g)
   if distance<.25-TOL:violations.append(dict(owner=name,net=n,gap_mm=distance,overlap_mm2=zone.intersection(g).area))
  if violations:fail('plane_clearance',layer=layer,violations=violations)
  # Copper flash shape/aperture must match each true pad/via, not merely contain center.
  flashes=[g for o,g in zip(parsed[layer].objects,geoms[layer]) if isinstance(o,Flash)]
  expected=[(n,g,name) for n,g,name in sources[layer] if name!='track']
  if len(flashes)!=len(expected):fail('flash_count',layer=layer,expected=len(expected),actual=len(flashes))
  unused=set(range(len(flashes)))
  for n,g,name in expected:
   matches=[i for i in unused if all(abs(a-b)<=TOL for a,b in zip(g.bounds,flashes[i].bounds)) and same_geometry(g,flashes[i])]
   if len(matches)!=1:fail('pad_via_aperture_mismatch',layer=layer,owner=name,matching=len(matches))
   else:unused.remove(matches[0])
  want=Counter(linekey(coord(one(t,'start')),coord(one(t,'end')),number(t,'width')) for t in children(pcb,'segment') if one(t,'layer')[1]==layer)
  got=Counter(linekey((o.x1,o.y1),(o.x2,o.y2),o.aperture.diameter) for o in parsed[layer].objects if isinstance(o,Line))
  if want!=got:fail('track_mismatch',layer=layer,missing=sum((want-got).values()),extra=sum((got-want).values()))
  copper=unary_union(geoms[layer]);gap=copper.distance(board.boundary)
  if gap<.25-TOL or copper.difference(board).area>1e-8:fail('copper_board_edge',layer=layer,gap_mm=gap)
  # Explicit conductor inter-net clearance, independent of native DRC.
  nets={n for n,g,name in sources[layer]};by_net={n:unary_union([g for nn,g,name in sources[layer] if nn==n]+([zone] if n==znet else [])) for n in nets}
  copper_by_layer[layer]=by_net
  names=sorted(nets)
  for i,n in enumerate(names):
   for m in names[i+1:]:
    distance=by_net[n].distance(by_net[m])
    if distance<.25-TOL:fail('different_net_clearance',layer=layer,net_a=n,net_b=m,gap_mm=distance)
  # Hole copper includes own-net exception ONLY for plated pad/via annulus.
  for hole in sum(expected_holes.values(),[]):
   for n,g in by_net.items():
    if hole in expected_holes['PTH'] and n==hole['net']:continue
    distance=max(0.0,Point(hole['x'],hole['y']).distance(g)-hole['d']/2)
    if distance<.25-TOL:fail('hole_copper_clearance',layer=layer,owner=hole['owner'],net=n,gap_mm=distance)
  metrics[layer]=dict(objects=len(geoms[layer]),regions=len(regions),min_board_edge_mm=gap,zone_net=znet)
 allholes=[]
 for plating,path in drills.items():
  d=ExcellonFile.open(path);actual=[]
  if str(d.import_settings.unit)!='mm':raise ValueError('Unsupported drill unit '+str(d.import_settings.unit))
  for o in d.objects:
   if not isinstance(o,Flash):raise ValueError('Unsupported drill routing/slot '+type(o).__name__)
   actual.append(drillkey(o.x,o.y,o.tool.diameter))
  want=Counter(drillkey(h['x'],h['y'],h['d']) for h in expected_holes[plating]);got=Counter(actual)
  if want!=got:fail('drill_mismatch',plating=plating,missing=list((want-got).elements()),extra=list((got-want).elements()))
  # Use ACTUAL exported holes for manufacture checks.
  allholes.extend([(x,y,d,Point(x,y).buffer(d/2,quad_segs=256)) for x,y,d in actual]);metrics[plating]=dict(drill_hits=len(actual))
 min_web=float('inf')
 for i,(x,y,d,g) in enumerate(allholes):
  edge=g.distance(board.boundary)
  if edge<.25-TOL or not board.covers(g):fail('hole_board_edge',index=i,gap_mm=edge)
  for j,(hx,hy,hd,h) in enumerate(allholes[i+1:],i+1):
   gap=math.hypot(x-hx,y-hy)-(d+hd)/2;min_web=min(min_web,gap)
   if gap<.25-TOL:fail('drill_web',a=i,b=j,gap_mm=gap)
 metrics['min_drill_web_mm']=min_web
 for layer in expected_masks:
  mask=unary_union(geoms[layer]);expected=unary_union(expected_masks[layer])
  if not same_geometry(mask,expected):fail('mask_geometry_mismatch',layer=layer,symmetric_difference_mm2=mask.symmetric_difference(expected).area,matched_component_hausdorff_mm=component_deviation(mask,expected))
  for owner_net,owner,opening in mask_owners[layer]:
   actual_opening=opening.intersection(mask)
   for other_net,copper_net in copper_by_layer[layer.replace('Mask','Cu')].items():
    if other_net==owner_net:continue
    overlap=actual_opening.intersection(copper_net).area
    if overlap>1e-8:fail('mask_to_foreign_copper',layer=layer,owner=owner,net=other_net,overlap_mm2=overlap)
  # Distinct serialized opening polygons; overlaps are not waived even same net.
  gs=geoms[layer];min_bridge=float('inf')
  for i,g in enumerate(gs):
   for h in gs[i+1:]:
    distance=g.distance(h);min_bridge=min(min_bridge,distance)
    if distance<.1-TOL:fail('mask_bridge',layer=layer,gap_mm=distance)
  silk_layer=layer.replace('Mask','SilkS');silk=unary_union(geoms[silk_layer]);distance=silk.distance(mask) if not silk.is_empty else None
  if distance is not None and distance<.1-TOL:fail('silk_mask_clearance',layer=silk_layer,gap_mm=distance,overlap_mm2=silk.intersection(mask).area)
  if not silk.is_empty and (silk.difference(board).area>1e-8 or silk.distance(board.boundary)<.1-TOL):fail('silk_board_edge',layer=silk_layer)
  metrics[layer]=dict(openings=len(gs),min_bridge_mm=min_bridge,silk_gap_mm=distance)
 for layer in expected_paste:
  actual=unary_union(geoms[layer]);expected=unary_union(expected_paste[layer])
  equal=(actual.is_empty and expected.is_empty) or (not actual.is_empty and not expected.is_empty and same_geometry(actual,expected))
  if not equal:fail('paste_geometry_mismatch',layer=layer,symmetric_difference_mm2=actual.symmetric_difference(expected).area)
  metrics[layer]=dict(objects=len(geoms[layer]),area_mm2=actual.area)
 return dict(passed=not errors,errors=errors,metrics=metrics,coordinate_contract='Gerber X=KiCad X; Gerber Y=-KiCad Y; no fitted offset/mirror',thresholds_mm={'copper_clearance':.25,'copper_edge':.25,'drill_web':.25,'hole_copper':.25,'mask_bridge':.1,'silk_mask':.1,'silk_edge':.1,'numerical_tolerance':TOL},file_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pcb_path,*files.values(),*drills.values()]},limitations=['Supported rect/circle pads and circular drills only; unsupported geometry fails closed.','Region topology interpreted by strict Ucamco parser, no buffer(0)/make_valid.','Not a full PCB fill equivalence proof: plane-to-conductor distances checked independently; native DRC/netlist parity also required.','Nominal geometry not plating, registration, thermal or complete module fit certification.'])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pcb',required=True,type=Path);ap.add_argument('--gerber-dir',required=True,type=Path);ap.add_argument('--report',required=True,type=Path);a=ap.parse_args()
 try:r=audit(a.pcb,a.gerber_dir)
 except Exception as e:r=dict(passed=False,errors=[dict(kind='parse_or_unsupported_geometry',exception=type(e).__name__,message=str(e))],traceback=traceback.format_exc())
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8');print(json.dumps({'passed':r['passed'],'errors':r['errors'][:15],'error_count':len(r['errors']),'report':str(a.report)},ensure_ascii=True,indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
