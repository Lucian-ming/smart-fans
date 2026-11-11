"""Independent semantic mutations of native manufacture exports; no production writes."""
from pathlib import Path
import argparse,sys,json,shutil
from gerbonara import GerberFile,ExcellonFile
from gerbonara.graphic_objects import Region,Flash,Line,Arc
from verify_revb_native_fabrication import audit,net
ap=argparse.ArgumentParser();ap.add_argument('--pcb',required=True,type=Path);ap.add_argument('--gerber-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
S=lambda value:value  # validate_revB_schematic.parse returns string atoms, not sexpdata.Symbol
assert net([S('pad'),[S('net'),7,'GND']],{7:'GND'})=='GND'
assert net([S('zone'),[S('net'),7]],{7:'GND'})=='GND'
assert net([S('zone'),[S('net'),'7']],{7:'GND'})=='GND'
assert net([S('zone'),[S('net'),'GND']],{})=='GND'
try:net([S('zone'),[S('net'),7]],{})
except ValueError:pass
else:raise AssertionError('Unmapped legacy net accepted')
results=[]
for case in ['baseline','copper_intrusion','shifted_drill','wrong_y_mirror']:
 directory=a.gerber_dir
 if case!='baseline':
  directory=a.out/case;shutil.copytree(a.gerber_dir,directory,dirs_exist_ok=True)
  if case=='shifted_drill':
   path=next(p for p in directory.glob('*-PTH.drl'))
   g=ExcellonFile.open(path);g.objects[0].x+=.20;g.save(path)
  else:
   path=next(directory.glob('*.gtl'));g=GerberFile.open(path)
   if case=='copper_intrusion':
    # Known Q1 base pin on this frozen candidate; synthetic ground region overlaps it.
    g.objects.append(Region.from_rectangle(133.7,-119.8,.6,.6))
   else:
    for o in g.objects:
     if isinstance(o,Region):o.outline=[(x,-y) for x,y in o.outline]
     elif isinstance(o,Flash):o.y=-o.y
     elif isinstance(o,(Line,Arc)):
      o.y1=-o.y1;o.y2=-o.y2
      if isinstance(o,Arc):o.cy=-o.cy;o.clockwise=not o.clockwise
     else:raise AssertionError(type(o))
   g.save(path)
 try:r=audit(a.pcb,directory)
 except Exception as e:
  r={'passed':False,'errors':[{'kind':'exception','message':str(e),'type':type(e).__name__}]}
 (a.out/(case+'.json')).write_text(json.dumps(r,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf8')
 kinds={e['kind'] for e in r['errors']}
 expected={'baseline':set(),'copper_intrusion':{'plane_clearance','different_net_clearance'},'shifted_drill':{'drill_mismatch'},'wrong_y_mirror':{'track_mismatch','copper_board_edge'}}[case]
 correct=r['passed'] if case=='baseline' else not r['passed'] and bool(kinds&expected)
 results.append({'case':case,'test_passed':correct,'audit_passed':r['passed'],'error_kinds':sorted(kinds)})
 print(json.dumps(results[-1]),flush=True)
(a.out/'test_summary.json').write_text(json.dumps({'passed':all(r['test_passed'] for r in results),'tests':results},indent=2),encoding='utf8')
if not all(r['test_passed'] for r in results):sys.exit(1)
