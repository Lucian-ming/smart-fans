"""Isolated serializer smoke tests. Synthetic copper/tracks are NOT production output."""
import ast
import math
import os
from pathlib import Path
import re
import zipfile
import sexpdata
from validate_revB_schematic import load_design, validate, parse, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/p1_serializer_smoke'
OUT.mkdir(parents=True, exist_ok=True)
components, tree = load_design()
nets_node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'NETS' for t in n.targets))
nets = ast.literal_eval(nets_node.value)
net_map = {name:n for n,name in nets}
pads = [dict(ref=c['ref'], pad=p[0], x=100+c['x']+p[1], y=100+c['y']+p[2], w=p[4], h=p[5], type=c['type'], net=p[3], nid=net_map.get(p[3],0)) for c in components for p in c['pads']]
ns = dict(os=os, re=re, math=math, zipfile=zipfile, COMPONENTS=components, NETS=nets, NET_MAP=net_map, PAD_RECORDS=pads, TRACKS=[(101,101,102,101,0.37,'F.Cu',2)], VIAS=[(102,102,0.8,0.4,1)], KEYHOLE_POLYS={k:[(101,101),(194,101),(194,194),(101,194)] for k in ('F.Cu','B.Cu')}, OFFSET_X=100, OFFSET_Y=100, BOARD_W=95, BOARD_H=95, CORNER_R=3, KICAD_DIR=str(OUT), FAB_DIR=str(OUT), DOWNLOAD_DIR=str(OUT))
functions = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('get_3d_model','export_kicad_pcb','export_kicad_sch','export_gerber_and_drill','build_safe_silkscreen','copper_zone_boundary')]
exec(compile(ast.Module(body=functions, type_ignores=[]), '<isolated serializing functions>', 'exec'), ns)
ns['export_kicad_sch']()
result = validate(OUT/'fan_ctrl_revB.kicad_sch', components)
assert result['pins'] == sum(len({p[0] for p in c['pads']}) for c in components if c['type'] != 'hole')
# Regression: break one wire start, preserving apparent proximity; must fail.
p = OUT/'fan_ctrl_revB.kicad_sch'
s = p.read_text(encoding='utf8')
m = re.search(r'\(wire \(pts \(xy ([-\d.]+) ([-\d.]+)\)', s)
bad = s[:m.start(1)] + str(float(m.group(1))+0.01) + s[m.end(1):]
negative = OUT/'negative_disconnected.kicad_sch'
negative.write_text(bad, encoding='utf8')
try:
    validate(negative, components)
except AssertionError:
    print('PASS negative control: 0.01mm displaced wire rejected')
else:
    raise AssertionError('Validator accepted disconnected wire')
ns['export_gerber_and_drill']()
from gerbonara import GerberFile
for ext in ('GTL','GBL','GTS','GBS','GTO','GBO','GKO'):
    g = GerberFile.open(OUT/f'fan_ctrl_revB.{ext}')
    print(ext, len(g.objects), 'parsed objects')
gko = (OUT/'fan_ctrl_revB.GKO').read_text()
assert gko.count('G03*') == 4 and 'G02*' not in gko
assert '%ADD' in (OUT/'fan_ctrl_revB.GTO').read_text()
ns['export_kicad_pcb']()
pcb_text = (OUT/'fan_ctrl_revB.kicad_pcb').read_text(encoding='utf8')
sexpdata.loads(pcb_text)
for n in walk(parse(pcb_text)):
    if n[0] in ('gr_text','property'):
        count = 2 if n[0] == 'gr_text' else 3
        assert all(isinstance(x,list) for x in n[count:]), n
print('PASS PCB S-expression parsing and text field structure')
print('PASS isolated serializer tests; synthetic copper artifacts are NOT production deliverables')
