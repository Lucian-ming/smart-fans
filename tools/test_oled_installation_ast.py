"""OLED first-prototype mounting contract, not a measured body fit certificate."""
import ast, copy, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/build_perfect_revB_v3.py').read_text(encoding='utf8'))
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENTS' for t in n.targets))
c={x['ref']:x for x in ast.literal_eval(node.value)}
def check(c):
 o=c['J_OLED']; assert (o['x'],o['y'])==(78.5,26.5)
 assert [(p[0],p[3]) for p in sorted(o['pads'],key=lambda p:p[1])]==[('4','I2C1_SDA'),('3','I2C1_SCL'),('2','+3.3V'),('1','GND')]
 assert all(abs(p[1]-x)<1e-9 and p[2]==0 for p,x in zip(o['pads'],[3.81,1.27,-1.27,-3.81]))
 l,r=c['J_VOICE_L'],c['J_VOICE_R'];assert l['y']==r['y']==44
 assert abs(r['x']-l['x']-25.4)<1e-9
check(c)
rejected=[]
for mode in ['old_direction','old_y','ASR_old_y']:
 b=copy.deepcopy(c)
 if mode=='old_direction': b['J_OLED']['pads']=[(p[0],-p[1],*p[2:]) for p in b['J_OLED']['pads']]
 elif mode=='old_y': b['J_OLED']['y']=55
 else: b['J_VOICE_L']['y']=b['J_VOICE_R']['y']=37
 try: check(b)
 except AssertionError: rejected.append(mode)
 else: raise AssertionError(mode)
result={'pass':True,'mounting_requirement_not_measurement':True,'oled_header':[78.5,26.5],'oled_body_direction':'-Y','ASR_center':[78.5,44],'negative_cases_rejected':rejected,'labels':[{'pin':p[0],'net':p[3],'x':78.5+p[1],'y':26.5} for p in c['J_OLED']['pads']],'limitations':['OLED body outline/pin-to-edge offsets not measured; must dry-fit and verify physical net labels before power','ASR nominal 30x28 outline assumes centered headers; full populated assembly not verified']}
(ROOT/'artifacts/oled_installation_ast_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
