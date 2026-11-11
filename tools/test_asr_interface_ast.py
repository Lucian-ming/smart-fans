"""AST-only ASR contract check; never executes the CAD generator."""
import ast
import copy
import json
from pathlib import Path
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'tools/build_perfect_revB_v3.py'
tree = ast.parse(source.read_text(encoding='utf8'))
data = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id in ('COMPONENTS', 'NETS')}

def validate(data):
    comps = {c['ref']: c for c in data['COMPONENTS']}
    assert 'MIC1' not in comps
    assert 23 not in dict(data['NETS']) and 'VOICE_MIC_P' not in dict(data['NETS']).values()
    assert all(p[3] != 'VOICE_MIC_P' for c in comps.values() for p in c['pads'])
    left, right = comps['J_VOICE_L'], comps['J_VOICE_R']
    assert abs(right['x'] - left['x'] - 25.4) < 1e-9
    assert left['y'] == right['y'] == 44.0
    expected = {
        'J_VOICE_L': ['GND', '+5V_ASR', 'NC', 'NC', 'ASR_TX1', 'ASR_RX1', 'NC', 'NC'],
        'J_VOICE_R': ['NC', 'GND', 'NC', 'NC', 'NC', 'NC', 'VOICE_SPK_N', 'VOICE_SPK_P'],
        'JP_ASR': ['+5V', '+5V_ASR'],
        'JP_ASR_TX': ['VOICE_TX', 'ASR_RX1'],
        'JP_ASR_RX': ['VOICE_RX', 'ASR_TX1'],
    }
    for ref, nets in expected.items():
        c = comps[ref]
        assert [p[3] for p in c['pads']] == nets, ref
        assert [p[0] for p in c['pads']] == [str(i+1) for i in range(len(nets))]
        if ref.startswith('J_VOICE'):
            assert 'PinSocket_1x08' in c['fp']
            assert all(abs(p[2] - (i-3.5)*2.54) < 1e-9 for i,p in enumerate(c['pads']))
    nets = dict(data['NETS'])
    assert len(set(nets.values())) == len(data['NETS']) == len(nets)
    assert [nets[x] for x in (33,34,35)] == ['+5V_ASR','ASR_RX1','ASR_TX1']
    # Each isolated ASR net has precisely a header endpoint and shunt endpoint.
    for net, refs in [('+5V_ASR', {'J_VOICE_L','JP_ASR'}), ('ASR_RX1', {'J_VOICE_L','JP_ASR_TX'}), ('ASR_TX1', {'J_VOICE_L','JP_ASR_RX'})]:
        endpoints = [(c['ref'],p[0]) for c in comps.values() for p in c['pads'] if p[3] == net]
        assert len(endpoints) == 2 and {r for r,p in endpoints} == refs
    assert comps['J_MCU_R']['pads'][6][3] == 'VOICE_TX'
    assert comps['J_MCU_R']['pads'][7][3] == 'VOICE_RX'
    assert [p[3] for p in comps['SPK1']['pads']] == ['VOICE_SPK_P','VOICE_SPK_N']
    allpads=[]
    for c in comps.values():
        for p in c['pads']:
            x,y=c['x']+p[1],c['y']+p[2]
            shape=Point(x,y).buffer(p[4]/2,quad_segs=32) if c['type'] in ('tht','hole') else box(x-p[4]/2,y-p[5]/2,x+p[4]/2,y+p[5]/2)
            allpads.append((c['ref'],p[0],shape))
    affected=set(expected)
    minimum=(999,None)
    for i,(ref,pid,geom) in enumerate(allpads):
        if ref not in affected: continue
        for other,opid,og in allpads:
            if other==ref: continue
            distance=geom.distance(og)
            if distance<minimum[0]: minimum=(distance,[ref,pid,other,opid])
            assert distance>=0.25-1e-6, (ref,pid,other,opid,distance)
    # Jumper access envelopes: 6 x 8 mm each, not under ASR board or other pads.
    cx=(left['x']+right['x'])/2
    module=box(cx-15,left['y']-14,cx+15,left['y']+14)
    for ref in ('JP_ASR','JP_ASR_TX','JP_ASR_RX'):
        c=comps[ref]; access=box(c['x']-3,c['y']-2,c['x']+3,c['y']+6)
        assert not access.intersects(module)
        assert all(not access.intersects(g) for r,p,g in allpads if r!=ref)
    return {'min_affected_pad_clearance_mm':minimum[0], 'closest_pair':minimum[1]}

result=validate(data)
negative=[]
for name,ref,idx,net in [('power_bypass','J_VOICE_L',1,'+5V'),('uart_bypass','J_VOICE_L',5,'VOICE_TX'),('swapped_uart','J_VOICE_L',4,'ASR_RX1'),('ldo_tied','J_VOICE_R',2,'+3.3V')]:
    bad=copy.deepcopy(data); c=next(c for c in bad['COMPONENTS'] if c['ref']==ref)
    pad=list(c['pads'][idx]);pad[3]=net;c['pads'][idx]=tuple(pad)
    try: validate(bad)
    except AssertionError: negative.append(name)
    else: raise AssertionError('negative case accepted: '+name)
result.update(pass_=True, negative_cases_rejected=negative, physical_row_pitch_mm=25.4,
              pin_pitch_mm=2.54, dimensional_evidence='user confirmation; not agent visual measurement',
              limitations=['AST pad/access checks only; reroute/final manufacturing validation required',
                           'External microphone is not provided; unsupported MIC1 and net23 removed',
                           'socket procurement and full module/USB envelope still require verification'])
output=ROOT/'artifacts/asr_interface_ast_validation.json'
output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
