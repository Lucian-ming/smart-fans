"""Audit real LTspice measurements; passing here is NOT a board release."""
from pathlib import Path
import hashlib, json, math, re
import sexpdata
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/simulation_review'
PCB = ROOT / 'hardware/kicad/fan_ctrl_revB.kicad_pcb'
def need(test, message):
    if not test: raise ValueError(message)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(name):
    path = OUT / (name + '.log')
    text = path.read_text(encoding='utf-8')
    need('LTspice 26.1.1' in text, 'Unexpected solver version')
    need(not re.search(r'Fatal|Measurement .*FAIL|singular matrix', text, re.I), 'Solver failure')
    steps = [dict((k.lower(), float(v)) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)', s)) for s in re.findall(r'^\.step (.+)$', text, re.M)]
    results = {}
    for name_, body in re.findall(r'Measurement: (\w+)\s*\n(.*?)(?=\nMeasurement:|\Z)', text, re.S):
        results[name_] = {int(i):float(v) for i,v in re.findall(r'^\s*(\d+)\s+([-+\d.eE]+)', body, re.M)}
    for name_, rows in results.items():
        need(set(rows)==set(range(1,len(steps)+1)), f'Incomplete measurement {name_}')
    return steps, results

def children(n, key): return [x for x in n if isinstance(x,list) and x and str(x[0])==key]
board = sexpdata.loads(PCB.read_text(encoding='utf-8'))
actual = {}
for fp in children(board,'footprint'):
    props = {str(x[1]):str(x[2]) for x in children(fp,'property')}
    if 'Reference' not in props:
        props.update({str(x[1]).title():str(x[2]) for x in children(fp,'fp_text')})
    ref = props.get('Reference')
    nets = set(str(n[2]) for p in children(fp,'pad') for n in children(p,'net'))
    actual[ref] = {'value':props.get('Value'), 'nets':sorted(nets)}
for ref, net in [('R_SCL','I2C1_SCL'),('R_SDA','I2C1_SDA')]:
    need(actual[ref]['value']=='4.7k' and set(actual[ref]['nets'])=={'+3.3V',net}, f'{ref} differs from model')
for ref, prefix in [('C1','100uF'),('C3','220uF'),('C_VM','220uF')]:
    need(actual[ref]['value'].startswith(prefix) and set(actual[ref]['nets'])=={'+5V','GND'}, f'{ref} differs from model')
steps, meas = parse('revb_i2c_rc_sweep')
need(len(steps)==18 and set(meas)=={'tr_30_70','vol','sink_low','final_high'}, 'Incomplete I2C run')
i2c = []
for i, params in enumerate(steps,1):
    tr = meas['tr_30_70'][i]
    expected = math.log(7/3)*params['rpull']*params['cbus']
    need(abs(tr/expected-1)<.01,'RC solver disagrees with analytic 30-70% rise')
    i2c.append({**params,'tr_30_70_s':tr,'analytic_tr_s':expected,'rise_only_standard_mode_pass':tr<=1e-6,'rise_only_fast_mode_pass':tr<=300e-9,'ideal_switch_vol_V':meas['vol'][i], 'ideal_sink_current_A':meas['sink_low'][i]})
need(any(x['rpull']==4700 and x['cbus']==4e-10 and not x['rise_only_standard_mode_pass'] for x in i2c),'Missing known failing RC case')
steps, meas = parse('revb_supply_loop_sweep')
need(len(steps)==18 and set(meas)=={'v_idle','v_min','v_loaded','v_release_max','max_source_current'}, 'Incomplete supply run')
supply = []
for i, params in enumerate(steps,1):
    loaded = meas['v_loaded'][i]
    need(abs(loaded-(params['vin']-2*params['rloop']))<.001,'DC sweep not consistent with Ohm law')
    supply.append({**params, **{key:vals[i] for key,vals in meas.items()},'assumed_bus_meets_TB6612_VM_4V5':meas['v_min'][i]>=4.5})
need(any(not x['assumed_bus_meets_TB6612_VM_4V5'] for x in supply),'Missing negative supply corner')
report = {'scope':'conditional_lumped_models_only','numerical_consistency_pass':True,'board_release_approved':False,'actual_pcb_sha256':sha(PCB),'bound_component_values':{r:actual[r] for r in ['R_SCL','R_SDA','C1','C3','C_VM']},'i2c_cases':i2c,'supply_cases':supply,'assumptions':['I2C bus capacitance is unknown; 50..800pF is a sweep, not measured parasitics.','Additional 4.7k module pullups are hypothetical; 2350/1566.67 ohms model two/three parallel resistors.','Ideal switch is not a vendor GPIO model; low level/current results do not certify IO sink capability.','Power total loop R=.05/.15/.30 ohms includes supply and return; all are assumed, not extracted or measured.','L=1uH, ESR=.05ohm, ideal input source and .25->2A loads are assumptions, not measured motor/servo behavior.','Bulk capacitance is lumped and scaled .8/1; distribution, ceramic DC bias, adapter current limit, fuse I2t and MOS switching are not modeled.','No AMS1117 closed-loop model, thermal model, reverse protection or firmware/system proof.'],'source_hashes':{str(p.relative_to(ROOT)):sha(p) for name in ['revb_i2c_rc_sweep','revb_supply_loop_sweep'] for p in [OUT/(name+'.cir'),OUT/(name+'.log'),OUT/(name+'.raw')]}}
(OUT/'conditional_simulation_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'numerical_consistency_pass':True,'board_release_approved':False,'i2c_cases':len(i2c),'i2c_standard_rise_failures':sum(not x['rise_only_standard_mode_pass'] for x in i2c),'i2c_fast_rise_failures':sum(not x['rise_only_fast_mode_pass'] for x in i2c),'supply_cases':len(supply),'supply_VM_corner_failures':sum(not x['assumed_bus_meets_TB6612_VM_4V5'] for x in supply),'supply_min_V':min(x['v_min'] for x in supply)},indent=2))
