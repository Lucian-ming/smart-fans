"""AST-only EC 2+3 interface tests. Does not import or run the board generator."""
import ast
import copy
import json
from pathlib import Path
from shapely.geometry import Point, box
ROOT = Path(__file__).resolve().parents[1]

def load():
    tree = ast.parse((ROOT/'tools/build_perfect_revB_v3.py').read_text(encoding='utf-8'))
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in ('COMPONENTS','NETS'):
                    out[t.id] = ast.literal_eval(n.value)
    return out

def check(d):
    parts = {c['ref']: c for c in d['COMPONENTS']}
    p = parts['J_ENC']
    expected = [('1',-1.27,-21.,'+3.3V',1.7,1.),('2',1.27,-21.,'GND',1.7,1.),
                ('3',-2.54,0.,'ENC_A',1.7,1.),('4',0.,0.,'GND',1.7,1.),('5',2.54,0.,'ENC_B',1.7,1.)]
    assert p['pads'] == expected, 'EC pad numbering/net/geometry mismatch'
    assert (p['x'],p['y']) == (71.,82.5), 'EC placement changed'
    assert next(p for p in parts['J_MCU_L']['pads'] if p[0]=='20')[3] == 'NC', 'PB12 must be NC'
    assert 'ENC_SW' not in {n for _,n in d['NETS']}, 'obsolete ENC_SW net'
    assert not any(p[3]=='ENC_SW' for c in parts.values() for p in c['pads']), 'obsolete SW pad'

def copper(c,p):
    _,dx,dy,_,w,h = p
    x,y = c['x']+dx,c['y']+dy
    if c['type'] in ('tht','hole'):
        return Point(x,y).buffer(w/2,quad_segs=64)
    return box(x-w/2,y-h/2,x+w/2,y+h/2)

def main():
    d=load();check(d)
    negatives=[]
    for name,idx,field,value in [('swaps_A_C',2,3,'GND'),('old_row_spacing',0,2,-21.7),('reverse_power',0,3,'GND'),('wrong_middle',3,3,'ENC_B')]:
        bad=copy.deepcopy(d); ec=next(c for c in bad['COMPONENTS'] if c['ref']=='J_ENC')
        row=list(ec['pads'][idx]);row[field]=value;ec['pads'][idx]=tuple(row)
        try: check(bad)
        except AssertionError: negatives.append(name)
        else: raise AssertionError('negative accepted: '+name)
    ec=next(c for c in d['COMPONENTS'] if c['ref']=='J_ENC')
    nearest=[]
    for p in ec['pads']:
        candidates=[]
        for c in d['COMPONENTS']:
            if c['ref']=='J_ENC':continue
            for q in c['pads']:
                candidates.append((copper(ec,p).distance(copper(c,q)),c['ref'],q[0]))
        gap,ref,pin=min(candidates)
        assert gap>=.25, (p[0],gap,ref,pin)
        nearest.append({'ec_pin':p[0], 'nearest_ref':ref,'nearest_pin':pin,'copper_gap_mm':gap})
    report={'passed':True,'negative_cases_rejected':negatives,'pad_clearance_to_other_components':nearest,
            'scope':'AST pads only; not routed copper or module-body assembly approval',
            'confirmed_by_user':'21mm group-center distance; top VCC/GND, bottom A/C/B',
            'body_warning':'OLED module extension direction/Z is not proven; positive-Y OLED body could overlap encoder module.'}
    (ROOT/'artifacts/ec23_interface_test.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
