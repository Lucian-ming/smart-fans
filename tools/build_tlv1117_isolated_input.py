"""Run the current generator in an isolated artifact root, never publish its legacy Gerbers."""
import ast
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tools/build_perfect_revB_v3.py'
OUT=ROOT/'artifacts/tlv1117_rebuild_input_v2'
if OUT.exists():
    raise SystemExit('Refusing to overwrite existing isolated build directory')
(OUT/'hardware/fabrication/validation').mkdir(parents=True)
tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
found=0
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROOT_DIR' for t in node.targets):
        node.value=ast.Constant(str(OUT));found+=1
if found!=1: raise RuntimeError('Expected exactly one ROOT_DIR assignment')
ast.fix_missing_locations(tree)
sys.path.insert(0,str(ROOT/'tools'))
exec(compile(tree,str(SOURCE),'exec'),{'__name__':'__main__','__file__':str(SOURCE)})
print('ISOLATED INPUT ONLY: use native converter; legacy Gerbers are not manufacturing deliverables.')
