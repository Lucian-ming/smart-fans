from pathlib import Path
import urllib.request
from pypdf import PdfReader
import io
sources={
 'tb6612':'https://toshiba.semicon-storage.com/info/docget.jsp?did=10660&prodName=TB6612FNG',
 'tb6612_mirror':'https://www.pololu.com/file/0J86/TB6612FNG.pdf',
 'i2c':'https://www.nxp.com/docs/en/user-guide/UM10204.pdf',
 'asr':'http://www.haohaodada.com/jpeguploadfile/twen/ASRPRO/ASRPROCoreV1.1.pdf',
}
for key,url in sources.items():
 try:
  data=urllib.request.urlopen(url, timeout=25).read()
  r=PdfReader(io.BytesIO(data))
  text='\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(r.pages))
  out=Path('artifacts/electrical_evidence');out.mkdir(exist_ok=True)
  (out/(key+'.pdf')).write_bytes(data)
  (out/(key+'.txt')).write_text(text,encoding='utf-8')
  print(key,url,len(r.pages),len(text))
 except Exception as e: print(key,type(e).__name__,str(e))
