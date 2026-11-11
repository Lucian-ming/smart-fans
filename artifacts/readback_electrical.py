from pathlib import Path
import sexpdata as s, json, math

def tag(n): return str(n[0]) if isinstance(n,list) and n else ''
def kids(n,t): return [x for x in n if tag(x)==t]
def one(n,t): return next(x for x in n if tag(x)==t)
root=s.loads(Path('hardware/kicad/fan_ctrl_revB.kicad_pcb').read_text(encoding='utf-8'))
result={}
for fp in kids(root,'footprint'):
 ref=next(str(x[2]) for x in kids(fp,'fp_text') if str(x[1])=='reference')
 if ref in ['J_TB_R','J_MCU_L','J_VOICE_L','R_SCL','R_SDA','D1','D2']:
  result[ref]={str(p[1]):str(one(p,'net')[2]) for p in kids(fp,'pad') if kids(p,'net')}
result['calculations']={'TB_VIH_at_5V':.7*5,'TB_VIH_at_3V3':.7*3.3,'buck_deltaI_12to5_47uH_150kHz':(12-5)*(5/12)/(47e-6*150e3),'I2C_4k7_Cmax_300ns_pF':300e-9/(.8473*4700)*1e12,'I2C_4k7_Cmax_1000ns_pF':1e-6/(.8473*4700)*1e12,'cap_220uF_1A_1ms_dV':1*.001/220e-6}
print(json.dumps(result,indent=2,ensure_ascii=False))
Path('artifacts/electrical_evidence/pcb_readback.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
