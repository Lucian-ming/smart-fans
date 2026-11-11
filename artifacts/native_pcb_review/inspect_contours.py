import ast,sys,math,json
from pathlib import Path
import numpy as np
import manifold3d as m3d
from shapely.geometry import Polygon,Point
sys.path.insert(0,str(Path('tools').resolve()))
from verify_revb_power import read_board
p,t,v,n=read_board(Path('hardware/kicad/fan_ctrl_revB.kicad_pcb'))
src=Path('tools/build_perfect_revB_v3.py').read_text(encoding='utf8'); tree=ast.parse(src)
funcs=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name in ('compute_copper_zone','copper_zone_boundary')]
f=next(f for f in funcs if f.name=='compute_copper_zone')
ix=next(i for i,a in enumerate(f.body) if isinstance(a,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='polys' for z in a.targets))
f.body=f.body[:ix+1]+[ast.Return(ast.Name('polys',ast.Load()))]
ns=dict(math=math,np=np,m3d=m3d,PAD_RECORDS=p,TRACKS=t,VIAS=v,CORNER_R=3,OFFSET_X=100,OFFSET_Y=100,BOARD_W=95,BOARD_H=95)
exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),'diagnostic','exec'),ns)
out={}
for layer in ['F.Cu','B.Cu']:
 polys=ns['compute_copper_zone'](layer)
 rows=[]
 for p in polys:
  a=float(np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])/2)
  rows.append({'signed_area':a,'bounds':Polygon(p).bounds,'contains_Q1':Polygon(p).contains(Point(134,119.5)),'contains_NC8':Polygon(p).contains(Point(139.88,146.35))})
 out[layer]={'outer_count':sum(x['signed_area']>0 for x in rows),'hole_count':sum(x['signed_area']<0 for x in rows),'contours':rows}
Path('artifacts/native_pcb_review/manifold_contours.json').write_text(json.dumps(out,indent=2),encoding='utf8')
for layer,d in out.items():print(layer,d['outer_count'],d['hole_count'],[r for r in d['contours'] if r['signed_area']>0 or r['contains_Q1'] or r['contains_NC8']])
