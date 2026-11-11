"""Independent electrical semantic regression, not a manufacturing release.
Extracts only literal components and SCH exporter; never imports the build module.
"""
import ast
import copy
import math
import os
import re
from pathlib import Path
import sexpdata
from validate_revB_schematic import validate

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'tools/build_perfect_revB_v3.py'
OUT = ROOT / 'artifacts/electrical_semantics_check'
EXPECTED = {
    # D1/D2 Buck and series Schottky were REMOVED in the 5V-only revision.
    'D3': {'A': 'BUZ_DRV', 'K': '+5V'},
    'D4': {'A': '+5V', 'K': 'LED_5V_K'},
    'D5': {'A': '+3.3V', 'K': 'LED_3V3_K'},
}

def nodes(n, kind):
    return [x for x in n if isinstance(x, list) and x and str(x[0]) == kind]

def one(n, kind):
    x = nodes(n, kind)
    assert len(x) == 1, (kind, x)
    return x[0]

def walk(n):
    yield n
    for x in n:
        if isinstance(x, list):
            yield from walk(x)

def check(components, sch):
    by_ref = {c['ref']: c for c in components}
    libs = {x[1]: x for x in nodes(one(sch, 'lib_symbols'), 'symbol')}
    instances = {next(p[2] for p in nodes(x, 'property') if p[1] == 'Reference'): x for x in nodes(sch, 'symbol')}
    for ref, want in EXPECTED.items():
        comp = by_ref[ref]
        pads = {p[0]: p for p in comp['pads']}
        assert pads['1'][3] == want['K'] and pads['2'][3] == want['A'], (ref, pads)
        assert pads['2'][1] < 0 < pads['1'][1], 'Original physical orientation changed'
        lib = libs[one(instances[ref], 'lib_id')[1]]
        pins = {one(p, 'name')[1]: p for p in walk(lib) if p and str(p[0]) == 'pin'}
        assert one(pins['K'], 'number')[1] == '1', ref
        assert one(pins['A'], 'number')[1] == '2', ref
        assert one(pins['A'], 'at')[1] < 0 < one(pins['K'], 'at')[1], ref
        # Cached graphic has the cathode bar at x=+1.27; ensure it stays on K side.
        bars = [p for p in walk(lib) if p and str(p[0]) == 'polyline' and len(one(p, 'pts')) == 3]
        assert any([xy[1:] for xy in one(p, 'pts')[1:]] == [[1.27, 1.27], [1.27, -1.27]] for p in bars), ref
    left = {p[0]: p[3] for p in by_ref['J_MCU_L']['pads']}
    right = {p[0]: p[3] for p in by_ref['J_MCU_R']['pads']}
    assert left['1'] == right['18'] == 'NC'
    assert right['20'] == 'GND'  # User's local schematic P3.20; physical mapping verified separately
    assert left['3'] == '+5V_MCU' and left['2'] == right['19'] == 'GND'
    assert sum(p[3] == '+5V_MCU' for c in (by_ref['J_MCU_L'], by_ref['J_MCU_R']) for p in c['pads']) == 1
    assert all(p[3] != '+5V' for c in (by_ref['J_MCU_L'], by_ref['J_MCU_R']) for p in c['pads'])
    assert not {'U2', 'L1', 'D1', 'D2'} & set(by_ref), 'Cancelled Buck parts must not return'
    assert not any(p[3].startswith('+12V') or p[3].startswith('XL1509') for c in components for p in c['pads'])
    def pn(ref):
        return {p[0]: p[3] for p in by_ref[ref]['pads']}
    assert pn('DC1') == {'1': '+5V_RAW', '2': 'GND'}
    assert pn('F1') == {'1': '+5V_RAW', '2': '+5V_FUSED'}
    assert pn('Q_PWR') == {'1': '+5V', '2': '+5V', '3': '+5V', '4': 'GND', '5': '+5V_FUSED', '6': '+5V_FUSED', '7': '+5V_FUSED', '8': '+5V_FUSED'}
    assert pn('JP_USB') == {'1': '+5V', '2': '+5V_MCU'}
    assert [(c['ref'], p[0]) for c in components for p in c['pads'] if p[3] == '+5V_MCU'] == [('JP_USB','2'), ('J_MCU_L','3')]
    assert one(instances['DC1'], 'lib_id')[1] == 'Connector_Generic:Conn_01x02'
    assert one(instances['F1'], 'lib_id')[1] == 'Device:Fuse'
    assert one(instances['Q_PWR'], 'lib_id')[1] == 'SmartFan:AO4409'
    power_lib = libs['SmartFan:AO4409']
    assert {one(p,'number')[1]:one(p,'name')[1] for p in walk(power_lib) if p and str(p[0]) == 'pin'} == {'1':'S','2':'S','3':'S','4':'G','5':'D','6':'D','7':'D','8':'D'}
    assert all(p[3] != '+3.3V' for c in (by_ref['J_MCU_L'], by_ref['J_MCU_R']) for p in c['pads'])

if __name__ == '__main__':
    tree = ast.parse(SRC.read_text(encoding='utf-8'))
    comp_node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'COMPONENTS' for t in n.targets))
    components = ast.literal_eval(comp_node.value)
    exporter = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'export_kicad_sch')
    OUT.mkdir(parents=True, exist_ok=True)
    ns = {'math': math, 'os': os, 're': re, 'COMPONENTS': components, 'KICAD_DIR': str(OUT)}
    exec(compile(ast.Module(body=[exporter], type_ignores=[]), '<isolated SCH exporter>', 'exec'), ns)
    ns['export_kicad_sch']()
    path = OUT / 'fan_ctrl_revB.kicad_sch'
    sch = sexpdata.loads(path.read_text(encoding='utf-8'))
    check(components, sch)
    result = validate(path, components)
    print('PASS D3..D5: emitted cache K=1/A=2; D1/D2/U2/L1 explicitly removed; 5V input/fuse/P-MOS/USB jumper topology checked')
    print('PASS BluePill: both 3V3 outputs isolated, R20 grounded, only L3 powered')
    print('PASS emitted wire/label connectivity:', {k: result[k] for k in ('symbols', 'pins', 'connected_pins', 'nc_pins', 'wire_segments', 'errors')})
    for fault in ('reversed_D3', 'MCU_R20_5V', 'parallel_3V3'):
        bad = copy.deepcopy(components)
        c = next(x for x in bad if x['ref'] == ('D3' if fault == 'reversed_D3' else 'J_MCU_R'))
        num = '1' if fault == 'reversed_D3' else ('20' if fault == 'MCU_R20_5V' else '18')
        for i, p in enumerate(c['pads']):
            if p[0] == num:
                q = list(p); q[3] = 'GND' if fault == 'reversed_D3' else ('+5V' if fault == 'MCU_R20_5V' else '+3.3V'); c['pads'][i] = tuple(q)
        try:
            check(bad, sch)
        except AssertionError:
            print('PASS negative control rejected:', fault)
        else:
            raise AssertionError('Negative control accepted: ' + fault)
    for fault, ref, pin, net in [('fuse_bypass', 'F1', '2', '+5V_RAW'), ('pmos_reversed', 'Q_PWR', '1', '+5V_FUSED'), ('usb_jumper_bypass', 'J_MCU_L', '3', '+5V')]:
        bad = copy.deepcopy(components)
        c = next(x for x in bad if x['ref'] == ref)
        c['pads'] = [tuple(list(p[:3]) + [net] + list(p[4:])) if p[0] == pin else p for p in c['pads']]
        try:
            check(bad, sch)
        except AssertionError:
            print('PASS negative control rejected:', fault)
        else:
            raise AssertionError('Power negative control accepted: ' + fault)
    bad_sch = copy.deepcopy(sch)
    lib = next(x for x in nodes(one(bad_sch, 'lib_symbols'), 'symbol') if x[1] == 'Device:D')
    p = next(p for p in walk(lib) if p and str(p[0]) == 'pin' and one(p, 'name')[1] == 'K')
    one(p, 'number')[1] = '2'
    try:
        check(components, bad_sch)
    except AssertionError:
        print('PASS negative control rejected: cached K number=2')
    else:
        raise AssertionError('Wrong cache pin accepted')
    print('NOT a full power/USB/module compatibility release; actual variants remain unverified.')
