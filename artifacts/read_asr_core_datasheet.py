from pathlib import Path
import requests
from pypdf import PdfReader
import sys
sys.stdout.reconfigure(encoding='utf-8')
u='https://haohaodada.com/jpeguploadfile/twen/ASRPRO/asr_pro_core.pdf'
p=Path('docs/hardware/sources/asr_pro_core_review.pdf')
if not p.exists():
    r=requests.get(u,timeout=45);r.raise_for_status();p.write_bytes(r.content)
for i,page in enumerate(PdfReader(p).pages):
    print(f'--- PAGE {i+1} ---\n{page.extract_text()}')
