"""Download public procurement datasheets into immutable evidence files."""
from pathlib import Path
import requests, fitz, hashlib, json
OUT=Path('D:/smart_fans/artifacts/procurement_review_20261104')
OUT.mkdir(exist_ok=True)
urls={
'AO4407A':'https://atta.szlcsc.com/upload/public/pdf/source/20130807/1457706632699.pdf',
'KF128_508':'https://atta.szlcsc.com/upload/public/pdf/source/20240821/65781D2669BFD48A107CF288CD3FBA7A.pdf',
'C15850':'https://atta.szlcsc.com/upload/public/pdf/source/20160218/1457707763339.pdf',
'female_2P':'https://atta.szlcsc.com/upload/public/pdf/source/20210301/C2718488_F4427B881E42CAA8DDB0B1C12B3A522C.pdf',
'female_3P':'https://atta.szlcsc.com/upload/public/pdf/source/20241230/F2FBC7E47B6625F1E2699C5ECB75FE88.pdf',
'header_2P':'https://atta.szlcsc.com/upload/public/pdf/source/20260506/D60A1DECEC4B48D75BB2DC37807D24EA.pdf',
}
manifest=[]
for name,url in urls.items():
    p=OUT/(name+'.pdf')
    if p.exists():
        data=p.read_bytes()
    else:
        r=requests.get(url,timeout=60); r.raise_for_status(); data=r.content
        if not data.startswith(b'%PDF'): raise ValueError((name,'not PDF'))
        p.write_bytes(data)
    doc=fitz.open(stream=data,filetype='pdf')
    text='\n'.join('PAGE '+str(i+1)+'\n'+page.get_text() for i,page in enumerate(doc))
    dest=OUT/(name+'.txt')
    if not dest.exists(): dest.write_text(text,encoding='utf-8')
    manifest.append(dict(name=name,url=url,sha256=hashlib.sha256(data).hexdigest(),pages=len(doc)))
    print(name,len(doc),text[:12000])
p=OUT/'download_manifest.json'
if not p.exists(): p.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
