import requests,json,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8');p=Path('artifacts/tb6612_web_sources')
for n,uid in [('same','6af32f99ba774cdfa2778fb8da9a823b'),('clone','1a8334bff644402591ee851ed35f6164')]:
 for tail in ['', '/proImages']:
  u='https://oshwhub.com/api/project/'+uid+tail
  r=requests.get(u,timeout=25);f=p/(n+('_images' if tail else '_detail')+'.json');f.write_text(r.text,encoding='utf8');print(u,r.status_code,r.text[:16000])
