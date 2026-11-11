"""Reproducible isolated native conversion. No production publishing.
Example: python artifacts/native_pcb_review/run_candidate_conversion.py --pcb hardware/kicad/fan_ctrl_revB.kicad_pcb --sch artifacts/native_sch_review/fan_ctrl_revB.kicad_sch --out artifacts/native_pcb_review/candidate
"""
from pathlib import Path
import subprocess,json,hashlib,sys,argparse
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--pcb',default='hardware/kicad/fan_ctrl_revB.kicad_pcb');ap.add_argument('--sch',default='artifacts/native_sch_review/fan_ctrl_revB.kicad_sch');ap.add_argument('--out',default='artifacts/native_pcb_review/candidate');a=ap.parse_args()
source_pcb=Path(a.pcb).resolve();source_sch=Path(a.sch).resolve();OUT=Path(a.out).resolve()
assert OUT.is_relative_to(ROOT/'artifacts'),'Only isolated artifacts output permitted'
assert not source_pcb.is_relative_to(OUT) and not source_sch.is_relative_to(OUT),'Inputs must be outside output directory'
OUT.mkdir(parents=True,exist_ok=True)
PY='D:/dev_tools/Python/python';K=Path('C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/bin');CLI=str(K/'kicad-cli.exe');KPY=str(K/'python.exe')
base=ROOT/'artifacts/native_pcb_review';sch=str(OUT/'fan_ctrl_revB.kicad_sch');pcb=str(OUT/'fan_ctrl_revB.kicad_pcb');net=str(OUT/'baseline.net')
protected=list({source_pcb,source_sch,ROOT/'hardware/kicad/fan_ctrl_revB.kicad_pcb',ROOT/'hardware/kicad/fan_ctrl_revB.kicad_sch'})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={str(p):sha(p) for p in protected}
script=lambda name:str(base/name)
commands=[
 ('baseline_netlist',[CLI,'sch','export','netlist','-o',net,str(source_sch)]),
 ('convert_sch',[PY,script('convert_candidate_sch.py'),'--sch',str(source_sch),'--out',str(OUT)]),
 ('netlist',[CLI,'sch','export','netlist','-o',str(OUT/'native.net'),sch]),
 ('connections',[PY,script('compare_candidate_connections.py'),'--before',net,'--out',str(OUT)]),
 ('convert_pcb',[KPY,script('convert_candidate_pcb.py'),'--pcb',str(source_pcb),'--out',str(OUT)]),
 ('erc',[CLI,'sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(OUT/'erc.json'),sch]),
 ('drc_parity',[CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','--exit-code-violations','--schematic-parity','--refill-zones','--save-board','-o',str(OUT/'drc_parity.json'),pcb]),
 ('invariance',[KPY,script('verify_candidate_invariance.py'),'--pcb',str(source_pcb),'--out',str(OUT)]),
 ('native_gerbers',[CLI,'pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--disable-aperture-macros','--output',str(OUT/'native_manufacturing')+'/',pcb]),
 ('native_drill',[CLI,'pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-report','--output',str(OUT/'native_manufacturing')+'/',pcb])]
results=[]
for name,args in commands:
 p=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (OUT/(name+'.log')).write_bytes(p.stdout);results.append({'step':name,'command':args,'exit_code':p.returncode});print(name,p.returncode,flush=True)
 if p.returncode:break
unchanged=hashes=={str(p):sha(p) for p in protected}
passed=unchanged and len(results)==len(commands) and all(x['exit_code']==0 for x in results)
outputs={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='run_summary.json'}
(OUT/'run_summary.json').write_text(json.dumps({'steps':results,'production_and_inputs_unchanged':unchanged,'baseline_hashes':hashes,'all_steps_pass':passed,'output_sha256':outputs,'release_authorized':False,'limitations':['Native ERC/DRC success is not physical assembly or thermal validation.','Snapshot libraries preserve source geometry; not independent package certification.','Solid ground connection increases soldering thermal load.']},indent=2),encoding='utf8')
if not passed:sys.exit(1)
