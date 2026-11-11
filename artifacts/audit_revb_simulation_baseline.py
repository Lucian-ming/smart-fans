"""Audit the frozen PCB against independently traced schematic connections."""
from pathlib import Path
import hashlib, json, sys
import sexpdata
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from publish_revb_pcb_prototype import validate_release

def children(n,k):
    return [x for x in n if isinstance(x,list) and x and str(x[0])==k]
def one(n,k):
    return children(n,k)[0]
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

pcb=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_pcb'
sch=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_sch'
expected={'pcb':'c9cb106cdc48e9b3e44ff9b6d379062e31b24f2d6fec1b29f22d64fc3b3264a1','sch':'ae4bb467b5398b3d5482221e21dfbe591e0b5d7721703dc5707e78e901f56ada'}
if digest(pcb)!=expected['pcb'] or digest(sch)!=expected['sch']:
    raise ValueError('Frozen baseline changed; do not reuse prior schematic trace')
root=sexpdata.loads(pcb.read_text(encoding='utf8'))
pins={}; components={}
for fp in children(root,'footprint'):
    props={str(p[1]):str(p[2]) for p in children(fp,'property')}
    ref=props['Reference']; entries=[]
    for pad in children(fp,'pad'):
        net=one(pad,'net'); name=str(net[2]) if int(net[1]) else ''
        key=(ref,str(pad[1])); pins.setdefault(key,set()).add(name)
        entries.append({'pin':key[1],'net':name,'pad_type':str(pad[2])})
    components[ref]={'value':props.get('Value'),'pads':entries}
trace=json.loads((ROOT/'artifacts/revB_schematic_validation.json').read_text(encoding='utf8'))
errors=[]; checked=set()
for row in trace['pin_results']:
    key=(row['ref'],row['pin']); checked.add(key)
    actual=set(row['actual']) if not row['no_connect'] else {''}
    if pins.get(key)!=actual:
        errors.append({'pin':key,'pcb':sorted(pins.get(key,set())),'schematic':sorted(actual)})
extras=sorted(set(pins)-checked)
# Four mounting holes have no electrical schematic symbol; explicitly record, do not hide.
for ref,pin in extras:
    if not ref.startswith('H') and not ref.startswith('M'):
        errors.append({'unexpected_pcb_only_pin':[ref,pin]})
v=ROOT/'hardware/fabrication/validation'
review=json.loads((v/'pcb_prototype_release_review.json').read_text(encoding='utf8'))
blocked=False
try:
    validate_release(ROOT,(v/'validation_summary.json').read_bytes(),review)
except ValueError as e:
    if str(e)!='Explicit prototype review required':
        raise
    blocked=True
if not blocked:
    errors.append({'error':'Publisher does not reject paused review'})
result={'baseline_sha256':expected,'checked_unique_schematic_pins':len(checked),'pcb_only_pins':extras,'errors':errors,'publisher_rejects_paused_review':blocked,'components':components,'scope':'static_cross_document_audit_not_circuit_simulation'}
out=ROOT/'artifacts/revb_simulation_baseline_audit.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='components'},ensure_ascii=True,indent=2))
raise SystemExit(bool(errors))
