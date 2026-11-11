from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
s=Path(__file__).with_name('build_perfect_revB_v3.py').read_text(encoding='utf-8')
s=s.split('# Helper functions for 3D models and authentic copper clearance computation')[0]
ns={};exec(compile(s,'route_prefix','exec'),ns)
out=Path(__file__).resolve().parents[1]/'artifacts'/'router_candidate.json'
out.write_text(json.dumps(dict(tracks=ns['TRACKS'],vias=ns['VIAS'])),encoding='utf-8')
print('Saved',out)
