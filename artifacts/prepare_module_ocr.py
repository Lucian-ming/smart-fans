from pathlib import Path
from PIL import Image
O=Path('D:/smart_fans/artifacts/user_module_sources')
items=[('oled',O/'pdf_0.png',(180,640,730,1030)),('tb',Path('E:/桌面/原理图/9-TB6612电机驱动/电机驱动模块使用说明.png'),(150,1030,500,1400)),('ec',Path('E:/桌面/原理图/11-旋转编码器/旋转编码器模块使用说明.png'),(200,2680,600,3240))]
for name,path,crop in items:
 im=Image.open(path).crop(crop); im=im.resize((im.width*3,im.height*3))
 for a in [0,90,180,270]:im.rotate(a,expand=True).save(O/f'{name}_{a}.png')
