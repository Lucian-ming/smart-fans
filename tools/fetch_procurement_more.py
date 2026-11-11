from pathlib import Path
import requests,fitz,hashlib,json,re
out=Path('D:/smart_fans/artifacts/procurement_review_20261104')
items={
'mcu_20P':'https://atta.szlcsc.com/upload/public/pdf/source/20240927/E668AFCBC52308B89CA29FFF8660355D.pdf',
'female_8P':'https://atta.szlcsc.com/upload/public/pdf/source/20231221/1CA800C6799ED97958773716FAA1BFFE.pdf',
'samsung_web':'https://weblib.samsungsem.com/cn/mlcc/mlcc-ec.do?partNumber=CL21A106KAYNNN',
'aos_package_web':'https://www.aosmd.com/packaging'}
manifest=[]
for name,url in items.items():
 p=out/(name+('.pdf' if '.pdf' in url else '.html'))
 data=p.read_bytes() if p.exists() else requests.get(url,timeout=50).content
 if not p.exists(): p.write_bytes(data)
 manifest.append({'name':name,'url':url,'sha256':hashlib.sha256(data).hexdigest()})
 if p.suffix=='.pdf':
  d=fitz.open(p);text='\n'.join(x.get_text() for x in d)
  t=out/(name+'.txt')
  if not t.exists():t.write_text(text,encoding='utf-8')
  image=out/(name+'.png')
  if not image.exists():d[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(image)
  print(name,text[:8000])
 else:
  text=data.decode('utf-8');print(name,'scripts',re.findall(r'<script[^>]*src=[\"\x27]([^\"\x27]+)',text))
p=out/'download_manifest_2.json'
if not p.exists():p.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
