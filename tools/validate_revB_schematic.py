"""Read emitted KiCad schematic and verify every pin's actual electrical net.
No import of the build script (which has top-level side effects). Optional isolated
schematic generation executes only AST-extracted COMPONENTS and export_kicad_sch.
"""
import argparse
import ast
import collections
import json
import math
from pathlib import Path
import re
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/build_perfect_revB_v3.py'

def load_design():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'COMPONENTS' for t in n.targets))
    return ast.literal_eval(node.value), tree

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, root = [], None
    for t in tokens:
        if t == '(':
            n = []
            if stack: stack[-1].append(n)
            else:
                assert root is None, 'Multiple roots'
                root = n
            stack.append(n)
        elif t == ')':
            assert stack, 'Unbalanced closing parenthesis'
            stack.pop()
        else:
            assert stack, 'Token outside root'
            stack[-1].append(json.loads(t) if t.startswith('"') else t)
    assert not stack, 'Unclosed expression'
    return root

def children(node, name):
    return [n for n in node if isinstance(n, list) and n and n[0] == name]

def one(node, name):
    rows = children(node, name)
    assert len(rows) == 1, (name, len(rows))
    return rows[0]

def walk(node):
    yield node
    for c in node:
        if isinstance(c, list): yield from walk(c)

def xy(node):
    return tuple(round(float(v), 5) for v in node[1:3])

def on_segment(p, a, b):
    return abs((p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0])) < 1e-6 and all(min(a[i], b[i])-1e-6 <= p[i] <= max(a[i], b[i])+1e-6 for i in (0, 1))

def validate(path, components):
    text = path.read_text(encoding='utf-8')
    assert '\\n' not in text, 'Literal newline escapes in output'
    sch = parse(text)
    for node in walk(sch):
        if node[0] == 'property':
            assert len(node) >= 3 and all(isinstance(v, list) for v in node[3:]), ('Malformed property', node)
    try:
        import sexpdata
        sexpdata.loads(text)
    except ImportError:
        pass
    assert sch[0] == 'kicad_sch'
    ids = [n[1] for n in walk(sch) if n[0] == 'uuid']
    for value in ids: uuid.UUID(value)
    assert len(ids) == len(set(ids)), 'Duplicate UUID'
    libraries = {n[1]: n for n in children(one(sch, 'lib_symbols'), 'symbol')}
    expected = {(c['ref'], p[0]): p[3] for c in components if c['type'] != 'hole' for p in c['pads']}
    pins, refs = {}, {}
    for inst in children(sch, 'symbol'):
        ref = next(n[2] for n in children(inst, 'property') if n[1] == 'Reference')
        lib = one(inst, 'lib_id')[1]
        refs[ref] = lib
        x, y, a = map(float, one(inst, 'at')[1:])
        assert not children(inst, 'mirror'), 'Mirroring unsupported by this validator'
        a = math.radians(a)
        unit = int(one(inst, 'unit')[1])
        for body in children(libraries[lib], 'symbol'):
            suffix = body[1].rsplit('_', 2)
            if len(suffix) == 3 and int(suffix[1]) not in (0, unit): continue
            for pin in children(body, 'pin'):
                px, py = map(float, one(pin, 'at')[1:3])
                # Rotate in the Y-up library domain, then invert Y on the sheet.
                point = (round(x + px*math.cos(a)-py*math.sin(a), 5), round(y-px*math.sin(a)-py*math.cos(a), 5))
                key = (ref, one(pin, 'number')[1])
                assert key not in pins, ('Duplicate pin', key)
                pins[key] = point
    assert set(pins) == set(expected), ('Pin membership mismatch', set(expected)-set(pins), set(pins)-set(expected))
    # 5V-only redesign replaces the old 3-pin barrel jack with a Phoenix 2-pin terminal.
    assert refs['DC1'] == 'Connector_Generic:Conn_01x02', refs['DC1']
    assert {key[1] for key in pins if key[0] == 'DC1'} == {'1', '2'}
    wires = [tuple(xy(n) for n in children(one(w, 'pts'), 'xy')) for w in children(sch, 'wire')]
    labels = [(xy(one(n, 'at')), n[1]) for n in children(sch, 'label')]
    ncs = {xy(one(n, 'at')) for n in children(sch, 'no_connect')}
    points = set(pins.values()) | {p for w in wires for p in w} | {p for p, _ in labels} | ncs
    parent = {p:p for p in points}
    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p
    def union(a,b): parent[find(a)] = find(b)
    for a,b in wires:
        for p in points:
            if on_segment(p, a, b): union(a,p)
    nets = collections.defaultdict(set)
    for p,name in labels: nets[find(p)].add(name)
    report, errors = [], []
    for key,p in pins.items():
        names = nets[find(p)]
        wired = any(on_segment(p,a,b) for a,b in wires)
        want = expected[key]
        start_error = min((math.dist(p,a) for a,b in wires), default=float('inf'))
        ok = (p in ncs and not wired and not names) if want == 'NC' else (wired and names == {want} and p not in ncs and start_error < 1e-6)
        row = {'ref':key[0], 'pin':key[1], 'xy':p, 'expected':want, 'actual':sorted(names), 'wired':wired, 'wire_start_error_mm':None if want == 'NC' else start_error, 'no_connect':p in ncs, 'pass':ok}
        report.append(row)
        if not ok: errors.append(row)
    result = {'file':str(path), 'symbols':len(refs), 'pins':len(pins), 'connected_pins':sum(r['wired'] for r in report), 'nc_pins':sum(r['no_connect'] for r in report), 'wire_segments':len(wires), 'errors':errors, 'pin_results':report}
    assert not errors, json.dumps(errors, ensure_ascii=False, indent=2)
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--schematic', type=Path, default=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_sch')
    p.add_argument('--generate-isolated', type=Path, help='Generate ONLY schematic to this directory, never run main build')
    p.add_argument('--report', type=Path)
    p.add_argument('--gto', type=Path)
    args = p.parse_args()
    components, tree = load_design()
    if args.generate_isolated:
        import os
        args.generate_isolated.mkdir(parents=True, exist_ok=True)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'export_kicad_sch')
        ns = dict(COMPONENTS=components, KICAD_DIR=str(args.generate_isolated), re=re, math=math, os=os)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), 'exec'), ns)
        args.schematic = Path(ns['export_kicad_sch']())
    result = validate(args.schematic, components)
    if args.gto:
        text = args.gto.read_text()
        blocks = re.split(r'G04 REF ([^ ]+) (BORDER|TEXT|NOTICE)\*', text)
        seen = set()
        for i in range(1, len(blocks), 3):
            ref, kind, body = blocks[i:i+3]
            if kind == 'NOTICE':
                continue
            assert len(re.findall(r'D01\*', body)) >= 2, (ref,kind,'No actual drawing')
            if kind == 'BORDER':
                segments = re.findall(r'X(-?\d+)Y(-?\d+)D02\*\s*X(-?\d+)Y(-?\d+)D01\*', body)
                assert len(segments) >= 2, (ref,'No real border segments')
                assert any(int(x1)!=int(x2) and int(y1)==int(y2) for x1,y1,x2,y2 in segments), (ref,'No horizontal border')
                assert any(int(y1)!=int(y2) and int(x1)==int(x2) for x1,y1,x2,y2 in segments), (ref,'No vertical border')
            seen.add((ref,kind))
        assert seen == {(c['ref'], k) for c in components for k in ('BORDER','TEXT')}
        result['gto_components'] = len(components)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'pin_results'}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
