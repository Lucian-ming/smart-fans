"""Reproducible isolated SCH semantic conversion; production inputs read-only."""
from pathlib import Path
import sexpdata as sx,copy,json,uuid,math,argparse
S=sx.Symbol
ap=argparse.ArgumentParser();ap.add_argument('--sch',default='artifacts/native_sch_review/fan_ctrl_revB.kicad_sch');ap.add_argument('--out',default='artifacts/native_pcb_review/candidate');args=ap.parse_args()
R=Path(args.out);R.mkdir(parents=True,exist_ok=True)
def rows(n,k):return [x for x in n if isinstance(x,list) and x and str(x[0])==k]
def one(n,k):return rows(n,k)[0]
def walk(n):
 if isinstance(n,list):
  yield n
  for x in n:yield from walk(x)
_uid_counter=0
def uid():
 global _uid_counter
 _uid_counter+=1
 return str(uuid.uuid5(uuid.NAMESPACE_URL,'fan-ctrl-revb-isolated-power-flag-'+str(_uid_counter)))
def node(t):return sx.loads(t)
src=Path(args.sch)
sch=sx.loads(src.read_text(encoding='utf8'));cache=one(sch,'lib_symbols')
origins=[];manifest={}
for inst in rows(sch,'symbol'):
 props={p[1]:p[2] for p in rows(inst,'property')};ref=props['Reference'];a=one(inst,'at');x,y=map(float,a[1:3]);nx=round(x/1.27)*1.27;ny=round(y/1.27)*1.27;dx=nx-x;dy=ny-y
 origins.append((x,y,dx,dy,ref))
 for sub in walk(inst):
  if sub and str(sub[0])=='at':sub[1]=round(float(sub[1])+dx,6);sub[2]=round(float(sub[2])+dy,6)
 props['Footprint']='RevB_Snapshot:Board_'+ref
 for p in rows(inst,'property'):
  if p[1]=='Footprint':p[2]=props['Footprint']
 manifest[ref]={'properties':props,'symbol_uuid':one(inst,'uuid')[1],'translation_mm':[dx,dy]}
# Every disconnected drawing cell is associated with its unique nearest symbol.
for item in sch:
 if not isinstance(item,list) or not item:continue
 typ=str(item[0])
 if typ not in ('wire','label','no_connect','junction'):continue
 p=one(one(item,'pts'),'xy') if typ=='wire' else one(item,'at')
 x,y=map(float,p[1:3]);dist=[((x-a)**2+(y-b)**2,dx,dy,ref) for a,b,dx,dy,ref in origins];d,dx,dy,ref=min(dist)
 if d>30**2:raise ValueError('Unassociated electrical item '+str(item))
 for sub in walk(item):
  if sub and str(sub[0]) in ('xy','at'):sub[1]=round(float(sub[1])+dx,6);sub[2]=round(float(sub[2])+dy,6)
 if typ=='label':
  item[0]=S('global_label');item.append([S('shape'),S('bidirectional')])
# Snapshot exact cached symbols into a real local library; no pin type edits.
idmap={}
lib=[S('kicad_symbol_lib'),[S('version'),20231120],[S('generator'),S('kicad_symbol_editor')]]
for sym in rows(cache,'symbol'):
 old=sym[1];base=old.split(':')[-1];new=old.replace(':','__');idmap[old]='RevB_Symbols:'+new
 for child in rows(sym,'symbol'):
  if not child[1].startswith(base+'_'):raise ValueError('Bad original prefix '+child[1])
  child[1]=new+child[1][len(base):]
 sym[1]=idmap[old];entry=copy.deepcopy(sym);entry[1]=new;lib.append(entry)
for inst in rows(sch,'symbol'):one(inst,'lib_id')[1]=idmap[one(inst,'lib_id')[1]]
# Installed official PWR_FLAG definition; its actual power_out pin is unchanged.
power=sx.loads(Path('C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/share/kicad/symbols/power.kicad_sym').read_text(encoding='utf8'))
flag=copy.deepcopy(next(x for x in rows(power,'symbol') if x[1]=='PWR_FLAG'));lib.append(copy.deepcopy(flag));flag[1]='RevB_Symbols:PWR_FLAG';cache.append(flag)
root_uuid=one(sch,'uuid')[1]
for i,net in enumerate(['+5V','GND'],1):
 label=next(x for x in rows(sch,'global_label') if x[1]==net);x,y=one(label,'at')[1:3];ref='#FLG0'+str(i)
 inst=node(f'(symbol (lib_id "RevB_Symbols:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid "{uid()}") (property "Reference" "{ref}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "PWR_FLAG" (at {x} {float(y)-3.81} 0) (effects (font (size 1.27 1.27)))) (pin "1" (uuid "{uid()}")) (instances (project "fan_ctrl_revB" (path "/{root_uuid}" (reference "{ref}") (unit 1)))))')
 sch.append(inst)
(R/'fan_ctrl_revB.kicad_sch').write_text(sx.dumps(sch),encoding='utf8')
(R/'RevB_Symbols.kicad_sym').write_text(sx.dumps(lib),encoding='utf8')
(R/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "RevB_Symbols")(type "KiCad")(uri "${KIPRJMOD}/RevB_Symbols.kicad_sym")(options "")(descr "Exact cached definitions plus official PWR_FLAG")))',encoding='utf8')
(R/'semantic_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('Converted',len(manifest),'symbols, global labels',len(rows(sch,'global_label')),'flags 2')
