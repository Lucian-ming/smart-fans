from pathlib import Path
import requests,re,fitz
out=Path('D:/smart_fans/artifacts/procurement_review_20261104')
for name,url in {'AOS_SO8':'https://www.aosmd.com/sites/default/files/res/packaging_information/SO8.pdf','samsung_detail':'https://weblib.samsungsem.com/mlcc/mlcc-ec-data-sheet.do?partNumber=CL21A106KAYNNN'}.items():
 p=out/(name+('.pdf' if name=='AOS_SO8' else '.html'))
 if not p.exists():
  r=requests.get(url,timeout=50);r.raise_for_status();p.write_bytes(r.content)
 if p.suffix=='.pdf':
  d=fitz.open(p);print(name,'\n'.join(x.get_text() for x in d))
  img=out/(name+'.png')
  if not img.exists():d[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(img)
 else:
  text=p.read_text(encoding='utf-8')
  for line in text.splitlines():
   if re.search(r'DCBias|chartData|url\s*:|\.js[\"\x27]|graphData|graphList',line):print(line[:700])
