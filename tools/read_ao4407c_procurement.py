from pathlib import Path
import requests,fitz,json,hashlib
out=Path('D:/smart_fans/artifacts/procurement_review_20261104')
url='https://atta.szlcsc.com/upload/public/pdf/source/20191212/C469397_0FA240FA8DBDAEB8A8E95B002A232449.pdf'
p=out/'AO4407C.pdf'
if not p.exists():
 r=requests.get(url,timeout=60);r.raise_for_status();p.write_bytes(r.content)
d=fitz.open(p);t='\n'.join(x.get_text() for x in d)
print(t[:14000]); print('SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
if not (out/'AO4407C.txt').exists():(out/'AO4407C.txt').write_text(t,encoding='utf-8')
