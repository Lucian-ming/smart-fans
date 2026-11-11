from pathlib import Path
from lxml import html
import sys,re
sys.stdout.reconfigure(encoding='utf8')
for p in Path('artifacts/tb6612_web_sources').glob('*.html'):
 s=p.read_text(encoding='utf8')
 if 'ç' in s[:1000]: s=s.encode('latin1').decode('utf8')
 r=html.fromstring(s)
 for e in r.xpath('//script|//style'):e.drop_tree()
 text=r.text_content();(p.with_suffix('.clean.txt')).write_text(text,encoding='utf8')
 print('\nPAGE',p.name)
 for m in re.finditer(r'TB6612|15\.24|2\.54|江协|尺寸|附件|原理图|PCB',text,re.I): print(text[max(0,m.start()-70):m.end()+180])
 print('LINKS',r.xpath('//a[contains(@href,"download") or contains(@href,"editor")]/@href'))
