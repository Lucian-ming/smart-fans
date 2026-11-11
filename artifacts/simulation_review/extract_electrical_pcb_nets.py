from pathlib import Path
import sexpdata as sx
import json, hashlib
ROOT=Path('D:/smart_fans')
p=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_pcb'
def tag(x,t): return isinstance(x,list) and bool(x) and str(x[0])==t
def children(x,t): return [v for v in x if tag(v,t)]
def one(x,t): return next((v for v in x if tag(v,t)),None)
b=sx.loads(p.read_text(encoding='utf8'))
fps={}
for f in children(b,'footprint'):
 r=next(v[2] for v in children(f,'property') if str(v[1])=='Reference')
 fps[r]={'value':next(v[2] for v in children(f,'property') if str(v[1])=='Value'),'pads':[{'pin':str(v[1]),'net':(one(v,'net') or [0,0,'NC'])[2]} for v in children(f,'pad')]}
result={'pcb_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'component_count':len(fps),'parts':fps,'scope':'Net assignments extracted from final PCB; not a new connectivity or circuit simulation PASS'}
out=ROOT/'artifacts/simulation_review/electrical_pcb_nets.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
for r in ['DC1','F1','Q_PWR','U3','C5','C6','C7','D5','R2','JP_USB','JP_ASR','JP_ASR_TX','JP_ASR_RX','J_TB_L','J_TB_R','R_STBY','J_MCU_L','J_MCU_R']:
 print(r, json.dumps(fps.get(r),ensure_ascii=False))
print('3V3 attached parts:')
for r,f in fps.items():
 if any(p['net']=='+3.3V' for p in f['pads']): print(r, f)
