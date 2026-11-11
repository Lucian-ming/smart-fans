from pathlib import Path
import json, requests
from lxml import html
urls={'C5258883':'https://www.lcsc.com/product-detail/C5258883.html','C2081':'https://www.lcsc.com/product-detail/C2081.html','C2718487':'https://www.lcsc.com/product-detail/C2718487.html'}
out=Path('artifacts/connector_part_evidence');out.mkdir(exist_ok=True)
for code,url in urls.items():
 try:
  r=requests.get(url,timeout=30);r.raise_for_status()
  t=html.fromstring(r.content)
  for n in t.xpath('//script|//style|//nav|//header|//footer'):n.drop_tree()
  text='\n'.join(x.strip() for x in t.text_content().splitlines() if x.strip())
  (out/(code+'.txt')).write_text(text,encoding='utf8')
  lines=text.splitlines(); hits=[i for i,s in enumerate(lines) if any(w.lower() in s.lower() for w in ['Pitch','Manufacturer','Package','2N3904','XH-2','2.54','2.5mm','Pin Number','Current Rating'])]
  selected=sorted({j for i in hits for j in range(max(0,i-1),min(len(lines),i+4))})
  print(code,url,json.dumps([lines[j] for j in selected],ensure_ascii=True))
 except Exception as e:print(code,type(e).__name__,str(e))
