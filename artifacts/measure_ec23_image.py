import cv2, numpy as np, json
from pathlib import Path
p=Path('D:/smart_fans/artifacts/user_module_sources/ec_0.png')
im=cv2.imdecode(np.fromfile(p,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
print('shape', im.shape)
for j,(x,y) in enumerate([(451,380),(565,375),(386,1381),(507,1380),(624,1381)]):
 roi=im[y-50:y+50,x-50:x+50]
 for threshold in [150,200,230]:
  _,b=cv2.threshold(roi,threshold,255,cv2.THRESH_BINARY)
  cs,_=cv2.findContours(b,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
  for c in cs:
   xx,yy,w,h=cv2.boundingRect(c)
   if 20<w<90 and 20<h<90:
    print('hole',j,threshold,[x-50+xx+w/2,y-50+yy+h/2,w,h])
