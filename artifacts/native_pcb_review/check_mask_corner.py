import sys
sys.path.insert(0,'tools')
from validate_revB_schematic import parse,children,one,xy
from pathlib import Path
from gerbonara import GerberFile
p=parse(Path('artifacts/native_pcb_review/candidate/fan_ctrl_revB.kicad_pcb').read_text(encoding='utf8'))
f=next(f for f in children(p,'footprint') if any(x[3]=='rect' for x in children(f,'pad')));q=next(x for x in children(f,'pad') if x[3]=='rect')
a=xy(one(f,'at'));b=xy(one(q,'at'));x=a[0]+b[0];y=-a[1]-b[1]
g=GerberFile.open('artifacts/native_pcb_review/candidate/native_manufacturing/fan_ctrl_revB-F_Mask.gts')
o=min(g.objects,key=lambda o:((o.bounding_box()[0][0]+o.bounding_box()[1][0])/2-x)**2+((o.bounding_box()[0][1]+o.bounding_box()[1][1])/2-y)**2)
print([(v[1],v[2]) for v in children(f,'property')][:2],q[:5],x,y);print(type(o).__name__,o.outline[:12],len(o.outline))
