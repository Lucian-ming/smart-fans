import requests,json,re,sys,concurrent.futures
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8');p=Path('artifacts/tb6612_web_sources')
urls=json.loads((p/'pid_same_scripts.json').read_text())
def go(u):
 f=p/u.split('/')[-1]
 try:
  if not f.exists():f.write_text(requests.get(u,timeout=15).text,encoding='utf8')
  s=f.read_text(encoding='utf8')
  for marker in ['24945:function','/pro/images','/projects/','pro.lceda.cn/api']:
   pos=s.find(marker)
   if pos>=0: print(f.name,marker,s[max(0,pos-150):pos+5000] if marker=='24945:function' else s[max(0,pos-150):pos+250])
 except Exception as e:print(type(e).__name__,u)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(go,urls))
