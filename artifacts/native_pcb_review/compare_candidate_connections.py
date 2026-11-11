from pathlib import Path
import json,sexpdata as sx,argparse
ap=argparse.ArgumentParser();ap.add_argument('--before',default='artifacts/native_sch_review/native.net');ap.add_argument('--out',default='artifacts/native_pcb_review/candidate');args=ap.parse_args()
R=Path(args.out)
def rows(n,k):return [x for x in n if isinstance(x,list) and x and str(x[0])==k]
def one(n,k):return rows(n,k)[0]
def read(path):
 root=sx.loads(path.read_text(encoding='utf8'));out={};nets={}
 for net in rows(one(root,'nets'),'net'):
  name=one(net,'name')[1]
  for pin in rows(net,'node'):
   ref=one(pin,'ref')[1];num=one(pin,'pin')[1]
   if ref.startswith('#'):continue
   key=ref+'.'+num
   if key in out:raise RuntimeError('Duplicate pin '+key)
   out[key]=('NC:'+key) if name.startswith('unconnected-') else name.lstrip('/')
   nets[key]=name
 return out,nets
old,_=read(Path(args.before));new,nets=read(R/'native.net')
report={'original_pin_count':len(old),'candidate_pin_count':len(new),'identical_connection_sets':old==new,'differences':[{'pin':p,'before':old.get(p),'after':new.get(p)} for p in sorted(set(old)|set(new)) if old.get(p)!=new.get(p)],'normalization':'Strip root sheet / prefix only; NC normalized by ref+pin; no merged nets accepted'}
(R/'connectivity_comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8')
assert old==new,report
(R/'native_pin_nets.json').write_text(json.dumps(nets,indent=2),encoding='utf8')
print(report)
