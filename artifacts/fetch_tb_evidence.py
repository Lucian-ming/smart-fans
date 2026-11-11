import requests
from pathlib import Path
from lxml import html
out=Path('artifacts/tb6612_web_sources');out.mkdir(exist_ok=True)
urls={
'sunfounder':'http://wiki.sunfounder.cc/index.php?title=TB6612_DC_Motor_Driver_Module',
'pid_clone':'https://oshwhub.com/zanfi1010/pid-ru-men-tao-jian-pcb-ban-fu-ke-jiang-xie-ke-ji',
'pid_same':'https://oshwhub.com/id_shift/pid-dian-ji-kong-zhi-_-zai-xian',
'lckfb':'https://openkits-wiki.easyeda.com/zh-hans/hspi-d133ebs/module/control/tb6612-motor-drive-module.html'}
for k,u in urls.items():
 try:
  r=requests.get(u,timeout=25);(out/(k+'.html')).write_text(r.text,encoding='utf8')
  root=html.fromstring(r.content);main=root.xpath('//main')
  text=(main[0] if main else root).text_content();(out/(k+'.txt')).write_text(text,encoding='utf8')
  print(k,r.status_code,len(r.content));print(text[-14000:] if k=='sunfounder' else text[:2000])
 except Exception as e:print(k,type(e).__name__,str(e))
