from pathlib import Path
import fitz,json
R=Path('E:/桌面/原理图');O=Path('D:/smart_fans/artifacts/user_module_sources');O.mkdir(exist_ok=True)
paths=[*R.glob('8*/*原理图/*4针*pdf'),*R.glob('8*/*原理图/*IIC*pdf*'),*R.glob('9*/*.pdf')]
for i,p in enumerate(paths):
 d=fitz.open(p); result={'source':str(p),'pages':[{'number':n+1,'text':pg.get_text(),'words':pg.get_text('words')} for n,pg in enumerate(d)]}
 (O/f'pdf_{i}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(str(p));print('\n'.join(pg.get_text() for pg in d)[:14000])
 if i<2:d[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(O/f'pdf_{i}.png')
