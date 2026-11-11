"""Check user-confirmed TB interface without executing the generator."""
import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_components():
    tree = ast.parse((ROOT / 'tools/build_perfect_revB_v3.py').read_text(encoding='utf-8-sig'))
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'COMPONENTS' for t in n.targets))
    return {c['ref']: c for c in ast.literal_eval(node.value)}

def check(c):
    left, right = c['J_TB_L'], c['J_TB_R']
    assert abs(right['x'] - left['x'] - 15.00) < 1e-9, 'row spacing must be user 15.00 mm'
    assert abs(right['y'] - left['y']) < 1e-9, 'rows misaligned'
    expected = [
        ['TB_PWMA', 'TB_AIN2', 'TB_AIN1', 'TB_STBY', 'GND', 'GND', 'GND', 'GND'],
        ['+5V', '+3.3V', 'GND', 'TB_AO1', 'TB_AO2', 'NC', 'NC', 'GND']]
    for row, nets in zip((left, right), expected):
        pads = sorted(row['pads'], key=lambda p:p[2])
        assert len(pads) == 8
        assert [p[0] for p in pads] == list(map(str, range(1,9))), 'top to bottom numbering'
        assert [p[3] for p in pads] == nets, 'pin function / net mismatch'
        assert all(abs(p[1]) < 1e-9 for p in pads), 'non-collinear row'
        assert all(abs(p[2] - (-8.89+i*2.54)) < 1e-9 for i,p in enumerate(pads)), 'pitch mismatch'
        assert row['fp'] == 'Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical'
    assert [p[3] for p in c['MOTO1']['pads']] == ['TB_AO1','TB_AO2'], 'motor output mismatch'
    assert c['C_VM']['pads'][0][3] == '+5V'

def replace_net(c, ref, i, net):
    p = list(c[ref]['pads'][i]); p[3] = net; c[ref]['pads'][i] = tuple(p)

if __name__ == '__main__':
    c = load_components(); check(c)
    mutations = {
        'assumed_15_24': lambda d: d['J_TB_R'].update(x=d['J_TB_L']['x']+15.24),
        'VM_12V': lambda d: replace_net(d,'J_TB_R',0,'+12V'),
        'VCC_5V': lambda d: replace_net(d,'J_TB_R',1,'+5V'),
        'reversed_AO': lambda d: replace_net(d,'J_TB_R',3,'TB_AO2'),
        'B_output_grounded': lambda d: replace_net(d,'J_TB_R',5,'GND'),
        'vertical_mirror': lambda d: d['J_TB_L'].update(pads=[(p[0],p[1],-p[2],*p[3:]) for p in d['J_TB_L']['pads']]),
    }
    negatives = {}
    for name, mutate in mutations.items():
        d = copy.deepcopy(c); mutate(d)
        try: check(d)
        except AssertionError as e: negatives[name] = {'rejected':True,'reason':str(e)}
        else: raise AssertionError('negative case accepted: '+name)
    report = {'pass':True,'evidence':'User measurement and pin order 2026-11-04; coarse 15 mm, not precision metrology','row_spacing_mm':15.0,'same_row_pitch_mm':2.54,'VM':'+5V','VCC':'+3.3V','motor':['TB_AO1','TB_AO2'],'negative_cases':negatives,'limitations':['AST only; no routing/manufacturing/full assembly verification','Module outline dimensions remain unverified; dry-fit before soldering']}
    (ROOT/'artifacts/tb_interface_ast_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=True))
