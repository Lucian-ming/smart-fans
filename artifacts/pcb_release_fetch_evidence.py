import requests,io,sys
from pypdf import PdfReader
sys.stdout.reconfigure(encoding='utf-8')
urls=[('ASR','https://haohaodada.com/jpeguploadfile/twen/ASRPRO/asr_pro_core.pdf'),('IND','https://atta.szlcsc.com/upload/public/pdf/source/20220324/2A0FB68E0EC6121FE8827F0972651A65.pdf')]
for name,url in urls:
 try:
  r=requests.get(url,timeout=25);r.raise_for_status(); p=PdfReader(io.BytesIO(r.content)); print(name,url);print('\n'.join(x.extract_text() for x in p.pages)[:25000])
 except Exception as e: print(name,type(e).__name__,str(e))
