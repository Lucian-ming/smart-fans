"""Read-only mapping from user's Altium top-side PCB to motherboard top-side."""
from pathlib import Path
import ast,json,math,sys
ROOT=Path(__file__).resolve().parents[1]
PINS={'P3':'VBAT PC13 PC14 PC15 PA0 PA1 PA2 PA3 PA4 PA5 PA6 PA7 PB0 PB1 PB10 PB11 NRST VCC3V3 GND GND'.split(),'P4':'VCC3V3 GND 5V PB9 PB8 PB7 PB6 PB5 PB4 PB3 PA15 PA12 PA11 PA10 PA9 PA8 PB15 PB14 PB13 PB12'.split()}
S=.0254
A=((0.,-S),(-S,0.))
def transform(x,y): return (47.5-S*(y-6022),40-S*(x-18541))
def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def main():
 d=json.loads((ROOT/'artifacts/core_altium_records.json').read_text(encoding='utf8')); rows=[]
 for name,index,ref,xwant in [('P4',7,'J_MCU_L',39.88),('P3',6,'J_MCU_R',55.12)]:
  pads=sorted((p for p in d['pads'] if p['component_index']==index),key=lambda p:int(p['name']))
  assert [p['name'] for p in pads]==list(map(str,range(1,21)))
  for n,p in enumerate(pads,1):
   x,y=transform(p['x_mil'],p['y_mil']);dy=24.13-(n-1)*2.54
   assert math.isclose(x,xwant,abs_tol=1e-8) and math.isclose(y,40+dy,abs_tol=1e-8)
   rows.append(dict(source=name,pin=n,signal=PINS[name][n-1],motherboard=ref,x=round(x,4),y=round(y,4),dx=0.,dy=round(dy,4)))
 det=A[0][0]*A[1][1]-A[0][1]*A[1][0];assert math.isclose(det,-S*S,abs_tol=1e-12)
 for i in range(2):
  for j in range(2): assert math.isclose(sum(A[k][i]*A[k][j] for k in range(2)),S*S if i==j else 0.,abs_tol=1e-12)
 src=[(17591,6322),(19491,6322),(17591,5722)]
 assert cross(*src)*cross(*(transform(*p) for p in src))<0
 assert cross(*src)*cross((39.88,15.87),(39.88,64.13),(55.12,15.87))>0
 assert transform(19442,6022)[1]<40
 snapshot={}
 for node in ast.parse((ROOT/'tools/build_perfect_revB_v3.py').read_text(encoding='utf8')).body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENTS' for t in node.targets): snapshot={c['ref']:c for c in ast.literal_eval(node.value)}
 mismatches=[]
 for r in rows:
  c=snapshot[r['motherboard']];p=next(p for p in c['pads'] if str(p[0])==str(r['pin']));r['snapshot_net']=p[3]
  if abs(c['x']+p[1]-r['x'])>1e-8 or abs(c['y']+p[2]-r['y'])>1e-8: mismatches.append(f"{r['motherboard']}.{r['pin']}")
 result=dict(source=d['source'],matrix_mm_per_mil=A,determinant=det,rows=rows,mapping_test_pass=True,old_mirror_negative_control_rejected=True,production_snapshot_position_mismatches=mismatches,limitation='PcbDoc Nets6 empty; logical labels independently transcribed from local schematic PDF, not extracted native netlist.')
 (ROOT/'artifacts/core_header_mapping.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 lines=['# 用户核心板40脚非镜像映射审计','','只读计算，不修改生产生成器。PcbDoc的125pad记录完整解析；Nets6为空，逻辑信号来自本地原理图PDF，不宣称提取原生网表。','','## 顶视变换','`X母板 = 47.5 - 0.0254*(Y_Altium - 6022)`','`Y母板 = 40.0 - 0.0254*(X_Altium - 18541)`','Altium单位mil/Y向上；母板mm/Y向下。矩阵[[0,-s],[-s,0]]，s=.0254，det=-.00064516，AᵀA=s²I：坐标约定翻转加刚体旋转，无物理镜像。','P4→J_MCU_L中心(39.88,40)，P3→J_MCU_R中心(55.12,40)；两排dy=24.13-(pin-1)*2.54；pin1在Y64.13，pin20在Y15.87。保留pin号/net，仅反转旧dy，必须重新布线。','USB原点(19442,6022)mil→(47.5,17.1146)mm，靠低Y。板框X17491..19591/Y5572..6472mil→母板X36.07..58.93/Y13.33..66.67，22.86×53.34mm。USB原点不是插口边缘，不代表外壳适配。','旧P4左/P3右且pin1向上pin20向下方案符号面积同号，是镜像，尽管pitch及排距正确。','','## 40脚表','|核心板|脚|PDF信号|母板座|X mm|Y mm|dx|dy mm|运行时net快照|','|---|---:|---|---|---:|---:|---:|---:|---|']
 for r in rows: lines.append(f"|{r['source']}|{r['pin']}|{r['signal']}|{r['motherboard']}|{r['x']:.2f}|{r['y']:.2f}|0|{r['dy']:.2f}|{r['snapshot_net']}|")
 lines+=['','## 验证边界',f'- 40脚坐标、2.54节距、15.24排距、正交性、USB低Y通过；旧镜像负例拒绝。主脚本位置不匹配数：{len(mismatches)}（运行时快照，非产物放行）。','- 核心板元件面向上，排针向下插母板顶面排母，不翻板。','- P3.20=GND非5V，已据本地PDF正式接GND；P4.1/P3.18为核心板3V3输出需隔离母板LDO；单5V入口P4.3。','- 未证明USB防反灌、负载能力或完整装配。','- [源解析](<D:/smart_fans/artifacts/read_core_altium.py>) / [原始记录](<D:/smart_fans/artifacts/core_altium_records.json>) / [测试](<D:/smart_fans/tools/test_core_header_mapping.py>) / [40脚JSON](<D:/smart_fans/artifacts/core_header_mapping.json>)']
 (ROOT/'artifacts/core_header_mapping.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
 print(json.dumps(dict(mapping_test_pass=True,pins=40,determinant=det,negative_control_rejected=True,production_snapshot_position_mismatches=len(mismatches))))
 if '--check-production' in sys.argv: assert not mismatches,mismatches
if __name__=='__main__': main()
