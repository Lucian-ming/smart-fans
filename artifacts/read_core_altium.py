from pathlib import Path
import olefile,struct,json,sys
sys.stdout.reconfigure(encoding='utf-8')
p=next(Path('E:/桌面/原理图/1-STM32F103C8T6核心板/PCB工程文件').glob('*核心板.PcbDoc'))
o=olefile.OleFileIO(p)
def strings(data):
 out=[]; i=0
 while i<len(data):
  n=struct.unpack_from('<I',data,i)[0]; i+=4
  out.append(data[i:i+n].decode('gb18030',errors='replace').strip('\x00')); i+=n
 return out
comps=strings(o.openstream('Components6/Data').read())
nets=strings(o.openstream('Nets6/Data').read())
print('NETS',nets)
b=o.openstream('Pads6/Data').read(); i=0; pads=[]
while i<len(b):
 typ=b[i]; i+=1; assert typ==2,(i,typ)
 sub=[]
 for k in range(6):
  n=struct.unpack_from('<I',b,i)[0];i+=4;sub.append(b[i:i+n]);i+=n
 body=sub[4]
 comp=struct.unpack_from('<H',body,7)[0]
 x,y=struct.unpack_from('<ii',body,13)
 name=sub[0][1:].decode('ascii',errors='replace')
 pad={'name':name,'component_index':comp,'x_mil':x/10000,'y_mil':y/10000,'net_id':struct.unpack_from('<H',body,3)[0],'body_hex':body.hex()}
 if comp in [0,6,7]: print(pad)
 pads.append(pad)
Path('D:/smart_fans/artifacts/core_altium_records.json').write_text(json.dumps({'source':str(p),'components':comps,'nets':nets,'pads':pads},ensure_ascii=False,indent=2),encoding='utf8')
print('pad_count',len(pads),'bytes_consumed',i,len(b))
