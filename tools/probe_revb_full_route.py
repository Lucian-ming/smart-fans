"""AST-isolated full route; writes only probe/cache artifacts, never builds PCB."""
import ast, hashlib, json, math, time
from pathlib import Path
from shapely.geometry import Point, LineString, box
from obstacle_router import route_board
from verify_revb_connectivity import check_networks
from verify_revb_power import audit_power
ROOT=Path(__file__).resolve().parents[1]
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
source=ROOT/'tools/build_perfect_revB_v3.py'
text=source.read_text(encoding='utf8'); values={}
for n in ast.parse(text).body:
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('COMPONENTS','NETS','OFFSET_X','OFFSET_Y','BOARD_W','BOARD_H'):
        values[n.targets[0].id]=ast.literal_eval(n.value)
names=dict(values['NETS']);netmap={s:i for i,s in names.items()};pads=[]
for c in values['COMPONENTS']:
    for p in c['pads']:
        pads.append(dict(ref=c['ref'],pad=p[0],x=round(values['OFFSET_X']+c['x']+p[1],4),y=round(values['OFFSET_Y']+c['y']+p[2],4),w=p[4],h=p[5],type=c['type'],nid=netmap.get(p[3],0)))
bounds=(values['OFFSET_X'],values['OFFSET_Y'],values['OFFSET_X']+values['BOARD_W'],values['OFFSET_Y']+values['BOARD_H'])
inputs=dict(pads=pads,bounds=bounds,net_names=names)
result=dict(scope='AST isolated full route, no PCB output',source_sha256=hashlib.sha256(text.encode()).hexdigest(),input_sha256=digest(inputs),inputs=inputs,router_sha256=hashlib.sha256((ROOT/'tools/obstacle_router.py').read_bytes()).hexdigest())
start=time.monotonic(); output=ROOT/'artifacts/revb_new_route_probe.json'; reportpath=ROOT/'artifacts/revb_new_router_report.json'
try:
    tracks,vias=route_board(pads,bounds,reportpath,net_names=names)
    report=json.loads(reportpath.read_text(encoding='utf8'))
    conductors=[];auditpads=[];holes=[]
    for i,p in enumerate(pads):
        key=f'p{i}';layers=['F.Cu'] if p['type']=='smd' else ['F.Cu','B.Cu']
        auditpads.append(dict(id=key,net=p['nid'],layers=layers))
        g=box(p['x']-p['w']/2,p['y']-p['h']/2,p['x']+p['w']/2,p['y']+p['h']/2) if p['type']=='smd' else Point(p['x'],p['y']).buffer(p['w']/2,quad_segs=64)
        conductors.extend((key,p['nid'],l,g) for l in layers)
        if p['type']!='smd':holes.append((key,p['x'],p['y'],p['h']))
    for i,t in enumerate(tracks):conductors.append((f't{i}',t[6],t[5],LineString([t[:2],t[2:4]]).buffer(t[4]/2,quad_segs=64)))
    for i,v in enumerate(vias):
        conductors.extend((f'via{i}',v[4],l,Point(v[0],v[1]).buffer(v[2]/2,quad_segs=64)) for l in ['F.Cu','B.Cu'])
        holes.append((f'v{i}',v[0],v[1],v[3]))
    gaps=[(math.dist(a[1:3],b[1:3])-(a[3]+b[3])/2,a[0],b[0]) for i,a in enumerate(holes) for b in holes[i+1:]]
    bad=[g for g in gaps if g[0]<.25-1e-8]
    copper=check_networks(auditpads,conductors,{})
    power=audit_power(pads,tracks,vias,names,report['power_rules'])
    result.update(tracks=tracks,vias=vias,router_report=report,copper_audit=copper,power_audit=power,hole_audit=dict(count=len(holes),minimum=min(gaps),violations=bad))
    result['passed']=not bad and not copper['clearance_violation_count'] and not copper['disconnected_net_count'] and power['passed']
except Exception as error:
    result.update(passed=False,error=repr(error))
result['elapsed_seconds']=time.monotonic()-start
result['route_sha256']=digest(dict(tracks=result.get('tracks'),vias=result.get('vias')))
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','tracks','vias','router_report','copper_audit')},indent=2))
raise SystemExit(0 if result['passed'] else 1)
