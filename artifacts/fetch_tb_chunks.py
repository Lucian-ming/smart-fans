import requests,json,re,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
p=Path('artifacts/tb6612_web_sources'); urls=json.loads((p/'pid_same_scripts.json').read_text()); urls=[u for u in urls if '/page-' in u or any('/'+n+'-' in u for n in ['6016','4032','5675','6402','469'])]
for u in urls:
 r=requests.get(u,timeout=20);s=r.text;(p/u.split('/')[-1]).write_text(s,encoding='utf8');print('FILE',u,len(s))
 for m in re.finditer(r'.{0,100}(?:pro\.lceda|/api/|documents|editor\?|project.*download).{0,180}',s):print(m.group(0))
