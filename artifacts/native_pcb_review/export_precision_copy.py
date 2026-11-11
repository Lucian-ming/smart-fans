from pathlib import Path
import subprocess,json,sys
r=Path('artifacts/native_pcb_review/candidate_precision_001');cli='C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe';pcb=str(r/'fan_ctrl_revB.kicad_pcb');sch=str(r/'fan_ctrl_revB.kicad_sch');out=str(r/'native_manufacturing')+'/'
commands=[['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(r/'erc_precision.json'),sch],['pcb','drc','--format','json','--all-track-errors','--severity-all','--exit-code-violations','--schematic-parity','--refill-zones','--save-board','-o',str(r/'drc_precision.json'),pcb],['pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--disable-aperture-macros','--output',out,pcb],['pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--output',out,pcb]]
results=[]
for i,args in enumerate(commands):
 p=subprocess.run([cli,*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(r/f'precision_step_{i}.log').write_bytes(p.stdout);results.append({'command':args,'exit_code':p.returncode});print(i,p.returncode,flush=True)
 if p.returncode:break
(r/'precision_export_results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
if len(results)!=4 or any(x['exit_code'] for x in results):sys.exit(1)
