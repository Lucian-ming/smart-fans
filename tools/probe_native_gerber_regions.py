"""Read-only probe of native KiCad Gerber regions against documented cut-in subset."""
from pathlib import Path
import json
from gerbonara import GerberFile
from gerbonara.graphic_objects import Region
from strict_copper_geometry import strict_region, AmbiguousCopperGeometry
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for path in sorted((ROOT/'artifacts/native_pcb_review/solid_native_gerbers').glob('*_Cu.*')):
    for i,o in enumerate(GerberFile.open(path).objects):
        if not isinstance(o,Region):continue
        try:
            p=strict_region(o,f'{path.name} Region[{i}]')
            rows.append(dict(file=path.name,index=i,supported=True,area_mm2=p.area))
        except AmbiguousCopperGeometry as e:
            rows.append(dict(file=path.name,index=i,supported=False,error=e.detail))
out=ROOT/'artifacts/strict_geometry_review/native_region_probe.json'
out.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows,indent=2))
