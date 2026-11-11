from pathlib import Path
import re,sys,json,requests
sys.stdout.reconfigure(encoding='utf8')
for n in ['pid_same','pid_clone']:
 s=Path('artifacts/tb6612_web_sources/'+n+'.html').read_text(encoding='utf8')
 for term in ['"attachments"','\\"attachments\\"','\\"documents\\"','\\"uuid\\"','\\"project\\"']:
  pos=s.find(term);print(n,term,pos,s[max(0,pos-1300):pos+1600])
 scripts=re.findall(r'<script[^>]+src="([^"]+)"',s)
 Path('artifacts/tb6612_web_sources/'+n+'_scripts.json').write_text(json.dumps(scripts,indent=2))
 print('scripts',scripts[-12:])
