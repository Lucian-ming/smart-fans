exec(open('artifacts/native_pcb_review/compare_geometry.py',encoding='utf8').read().split('for folder in')[0])
def winding(coords,p):
 x,y=p; wn=0; crossings=0
 for a,b in zip(coords,coords[1:]+coords[:1]):
  cross=(b[0]-a[0])*(y-a[1])-(x-a[0])*(b[1]-a[1])
  if a[1]<=y<b[1] and cross>0:wn+=1
  elif b[1]<=y<a[1] and cross<0:wn-=1
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:crossings+=1
 return {'winding':wn,'even_odd_filled':bool(crossings%2)}
result={}
for z in children(r,'zone'):
 coords=[xy(p) for p in children(one(one(z,'filled_polygon'),'pts'),'xy')]
 result[str(one(z,'layer')[1])]={k:winding(coords,v) for k,v in points.items()}
print(json.dumps(result,indent=2));(ROOT/'winding_evidence.json').write_text(json.dumps(result,indent=2),encoding='utf8')
