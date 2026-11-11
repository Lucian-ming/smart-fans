import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from validate_revB_schematic import parse,one,children,xy
from shapely.geometry import Polygon,Point
from shapely.validation import explain_validity
from shapely.ops import unary_union
from gerbonara import GerberFile
from gerbonara.graphic_objects import Region
ROOT=Path('artifacts/native_pcb_review')
r=parse(Path('hardware/kicad/fan_ctrl_revB.kicad_pcb').read_text(encoding='utf8'))
out={'zones':{},'gerbers':{}}
points={'BUZ_BASE_Q1':[134,119.5],'BUZ_BASE_R10':[134.85,115],'MCU_NC8':[139.88,146.35],'MCU_NC15':[139.88,128.57],'BUZZER_CTRL_via':[156.2,109.9]}
for z in children(r,'zone'):
 name=str(one(z,'layer')[1]); raw=Polygon([xy(p) for p in children(one(one(z,'filled_polygon'),'pts'),'xy')]); fixed=raw.buffer(0)
 out['zones'][name]={'valid':raw.is_valid,'validity':explain_validity(raw),'area':raw.area,'fixed_area':fixed.area,'fixed_type':fixed.geom_type,'points':{k:{'distance':fixed.distance(Point(v)),'contains':fixed.contains(Point(v))} for k,v in points.items()}}
for folder in [Path('hardware/fabrication/gerber_revB'),ROOT/'original_native_gerbers',ROOT/'refilled_native_gerbers']:
 for path in folder.glob('*'):
  if path.suffix.lower() not in ('.gtl','.gbl'):continue
  g=GerberFile.open(path); regions=[o for o in g.objects if isinstance(o,Region)]
  data=[];shapes=[]
  for o in regions:
   p=Polygon(o.outline); f=p.buffer(0);shapes.append(f)
   data.append({'vertices':len(o.outline),'valid':p.is_valid,'validity':explain_validity(p),'area':p.area,'polarity_dark':o.polarity_dark})
  shape=unary_union(shapes)
  sy=-1 if 'native_gerbers' in str(folder) else 1
  out['gerbers'][str(path)]={'region_count':len(data),'invalid_count':sum(not d['valid'] for d in data),'regions':data,'points':{k:{'distance_to_regions':shape.distance(Point(v[0],sy*v[1])),'inside_region':shape.contains(Point(v[0],sy*v[1]))} for k,v in points.items()}}
(ROOT/'geometry_comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(out,ensure_ascii=True,indent=2))
