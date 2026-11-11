from pathlib import Path
import hashlib,json,math,zipfile
from pypdf import PdfReader
base=Path('C:/Users/Lucian/AppData/Local/Programs/ADI/LTspice')
out=Path('D:/smart_fans/artifacts/simulation_review')
files=[base/'LTspice.exe',base/'License.txt',Path('C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/bin/ngspice.dll'),out/'rc_solver_baseline.cir',out/'rc_solver_baseline.log',out/'rc_solver_baseline.raw']
print(json.dumps({str(p):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files},indent=2))
print('LICENSE PDF TEXT\n'+ '\n'.join(p.extract_text() for p in PdfReader(base/'License.pdf').pages)[:16000])
print('EXACT MODEL ARCHIVE HITS')
with zipfile.ZipFile(base/'lib.zip') as z:
 hits=[]
 for n in z.namelist():
  if n.lower().endswith(('.mos','.lib','.sub','.cir','.mod')):
   b=z.read(n).lower()
   if b'ao4409' in b or b'ams1117' in b: hits.append(n)
 print(hits)
print('RC analytical',1-math.exp(-1),1-math.exp(-5))
