from pathlib import Path
import re,json,requests
out=Path('D:/smart_fans/artifacts/procurement_review_20261104')
s=(out/'aos_package_web.html').read_text(encoding='utf-8')
m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',s)
if m:
 data=json.loads(m[1])
 def walk(x):
  if isinstance(x,dict):
   if any(isinstance(v,str) and v in ('SO-8','SO8','SOIC-8') for v in x.values()):print(json.dumps(x,ensure_ascii=False)[:14000])
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(data)
for name,path in [('samsung_grid','/resources/cn/js/mlcc/setgrid_mlcc_ec.js'),('samsung_chart','/resources/cn/js/mlcc/chart_setting_mlcc_ec.js'),('samsung_common','/resources/cn/js/common_chart.js?update=260428')]:
 p=out/(name+'.js')
 if not p.exists():
  r=requests.get('https://weblib.samsungsem.com'+path,timeout=45);r.raise_for_status();p.write_text(r.text,encoding='utf-8')
 s=p.read_text(encoding='utf-8')
 print(name)
 for line in s.splitlines():
  if re.search(r'url\s*:|dc.?bias|\.do[\"\x27]',line,re.I):print(line[:450])
