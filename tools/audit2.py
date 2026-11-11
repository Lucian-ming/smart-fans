import re,json,sys
src=open("hardware/kicad/fan_ctrl_revB.kicad_pcb",encoding="utf-8").read()

def tokenize(s):
    return re.findall(r'\(|\)|"(?:[^"\]|\.)*"|[^\s()]+', s)
def parse(toks,i=0):
    assert toks[i]=='('
    out=[];i+=1
    while toks[i]!=')':
        if toks[i]=='(':
            node,i=parse(toks,i); out.append(node)
        else:
            t=toks[i]
            if t.startswith('"'): t=t[1:-1]
            out.append(t); i+=1
    return out,i+1
tree,_=parse(tokenize(src),0)

def find_all(node,name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]
def get(node,name):
    r=find_all(node,name); return r[0] if r else None

nets={}
for n in find_all(tree,'net'):
    if len(n)>=3 and n[1].isdigit(): nets[int(n[1])]=n[2]

fps=[];segs=[];vias=[];zones=[]
for c in tree:
    if not isinstance(c,list): continue
    if c[0]=='footprint':
        at=get(c,'at'); ref=None;val=None
        for t in c:
            if isinstance(t,list) and t[0]=='fp_text' and t[1]=='reference': ref=t[2]
            if isinstance(t,list) and t[0]=='fp_text' and t[1]=='value': val=t[2]
        fx,fy,frot=float(at[1]),float(at[2]),float(at[3]) if len(at)>3 else 0
        pads=[]
        for p in find_all(c,'pad'):
            pat=get(p,'at'); px,py=float(pat[1]),float(pat[2])
            sz=get(p,'size'); net=get(p,'net'); dr=get(p,'drill')
            pads.append(dict(num=p[1],x=fx+px,y=fy+py,dx=px,dy=py,
                w=float(sz[1]),h=float(sz[2]),type=p[2],shape=p[3],
                net=int(net[1]) if net else 0,
                netname=(net[2] if net and len(net)>2 else ""),
                drill=float(dr[1]) if dr and dr[1]!='oval' else 0))
        fps.append(dict(ref=ref,val=val,x=fx,y=fy,rot=frot,lib=c[1],pads=pads))
    elif c[0]=='segment':
        s=get(c,'start');e=get(c,'end')
        segs.append(dict(x1=float(s[1]),y1=float(s[2]),x2=float(e[1]),y2=float(e[2]),
                         w=float(get(c,'width')[1]),layer=get(c,'layer')[1],net=int(get(c,'net')[1])))
    elif c[0]=='via':
        a=get(c,'at'); vias.append(dict(x=float(a[1]),y=float(a[2]),net=int(get(c,'net')[1]),
                         size=float(get(c,'size')[1]),drill=float(get(c,'drill')[1])))
    elif c[0]=='zone':
        z=dict(net=int(get(c,'net')[1]),layer=get(c,'layer')[1],
               filled=len(find_all(c,'filled_polygon')))
        zones.append(z)
edges=[]
for c in tree:
    if isinstance(c,list) and c[0] in ('gr_line','gr_arc') and get(c,'layer') and get(c,'layer')[1]=='Edge.Cuts':
        edges.append(dict(kind=c[0],s=get(c,'start'),m=get(c,'mid'),e=get(c,'end')))

print("== BOARD ==")
print("footprints",len(fps),"pads",sum(len(f['pads']) for f in fps),"segs",len(segs),"vias",len(vias),"zones",zones)
xs=[p['x'] for f in fps for p in f['pads']]
ys=[p['y'] for f in fps for p in f['pads']]
print("pad bbox x[%.3f,%.3f] y[%.3f,%.3f]"%(min(xs),max(xs),min(ys),max(ys)))
print("== NETS ==")
from collections import defaultdict
pd=defaultdict(list);sd=defaultdict(int);vd=defaultdict(int)
for f in fps:
    for p in f['pads']: pd[p['net']].append((f['ref'],p['num'],p['netname']))
for s in segs: sd[s['net']]+=1
for v in vias: vd[v['net']]+=1
for n in sorted(nets):
    print(f"net {n:2d} {nets[n]:14s} pads={len(pd[n]):3d} segs={sd[n]:3d} vias={vd[n]:2d}")
print("net0 pads:",len(pd[0]))
for f in fps:
    print(f"\n## {f['ref']} {f['val']} at ({f['x']:.2f},{f['y']:.2f}) rot{f['rot']} lib={f['lib']} pads={len(f['pads'])}")
    for p in f['pads']:
        print(f"   {p['num']:>3s} {p['type']:9s}{p['shape']:9s} abs({p['x']:7.2f},{p['y']:7.2f}) rel({p['dx']:+6.2f},{p['dy']:+6.2f}) {p['w']}x{p['h']} net{p['net']} {p['netname']}")
json.dump(dict(fps=fps,segs=segs,vias=vias,zones=zones,nets=nets),open("tools/revb2.json","w"),ensure_ascii=False)
