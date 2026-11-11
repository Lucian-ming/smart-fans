"""Read COMPONENTS/NETS via AST and route only power trunks, never full build."""
import ast
import hashlib
import json
from pathlib import Path
from obstacle_router import route_power_backbone
from verify_revb_power import audit_power
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'tools/build_perfect_revB_v3.py'
text=source.read_text(encoding='utf8');tree=ast.parse(text);values={}
for n in tree.body:
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('COMPONENTS','NETS','OFFSET_X','OFFSET_Y','BOARD_W','BOARD_H'):
        values[n.targets[0].id]=ast.literal_eval(n.value)
netmap={s:i for i,s in values['NETS']};names=dict(values['NETS']);pads=[]
for c in values['COMPONENTS']:
    for p in c['pads']:
        pads.append(dict(ref=c['ref'],pad=p[0],x=round(values['OFFSET_X']+c['x']+p[1],4),y=round(values['OFFSET_Y']+c['y']+p[2],4),w=p[4],h=p[5],type=c['type'],nid=netmap.get(p[3],0)))
bounds=(values['OFFSET_X'],values['OFFSET_Y'],values['OFFSET_X']+values['BOARD_W'],values['OFFSET_Y']+values['BOARD_H'])
output=ROOT/'artifacts/power_layout_probe.json'
result=dict(source_sha256=hashlib.sha256(text.encode('utf8')).hexdigest(),scope='Power-only snapshot; not a full board build',pads=pads,net_names=names,vias=[])
try:
    tracks,report=route_power_backbone(pads,names,bounds)
    result.update(tracks=tracks,power_rules=report,audit=audit_power(pads,tracks,[],names,report))
except RuntimeError as error:
    result['error']=str(error)
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ('pads','tracks','power_rules')},indent=2))
raise SystemExit(1 if result.get('error') or not result['audit']['passed'] else 0)
