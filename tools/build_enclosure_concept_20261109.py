"""Independent visual concept; not a production enclosure or fit-certified STL."""
from pathlib import Path
import json, math, zipfile
import numpy as np
import trimesh
from manifold3d import Manifold as M
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/concept_20261109'
OUT.mkdir(parents=True,exist_ok=True)
W=107.; H=42.; WALL=2.; OFFSET=6.; SPLIT=12.
def cube(s,p=(0,0,0)):return M.cube(s).translate(p)
def cyl(h,r,p):return M.cylinder(h,r,r,circular_segments=64).translate(p)
def above(z=42):return cube([220,220,100],[-110,-110,0]).rotate([-25,0,0]).translate([53.5,65,z])
outer=cube([W,W,H])-above()
inner=cube([W-4,W-4,60],[2,2,2])-above(H-2/math.cos(math.radians(25)))
shell=outer-inner
# Four PCB posts, 95mm board shifted by (6,6); nominal underside Z7.
for x,y in [(11,11),(96,11),(11,96),(96,96)]:
 shell+=cyl(5,3.2,[x,y,2])
 shell-=cyl(6,1.2,[x,y,2])
# Rectangular rear cable opening: placeholder, not a terminal fitted cutout.
shell-=cube([14,6,8],[14,-2,10])
# OLED vertical viewing opening in flat rear deck. Centre provisional from pin row.
shell-=cube([25,14,30],[72,14,20])
# Horizontal button pads on slope, vertical bores. Centres follow PCB headers only.
for x in [40,55.5]:
 shell+=cyl(7,6,[x,88.5,29])
 shell-=cyl(25,3.6,[x,88.5,15])
# Encoder shaft placeholder: centre between module headers, NOT measured axis.
shell-=cyl(40,4.5,[77,78,10])
# Gesture aperture follows header X; actual sensor centre unknown.
shell-=cube([10,10,35],[17,73,15])
# Cosmetic ventilation slots on side; no IP or thermal certification.
for y in [32,40,48,56]:shell-=cube([6,3,12],[-2,y,17])
lid,base=shell.split_by_plane([0,0,1],SPLIT)
# Shallow locating ledge in the upper shell, clearance 0.3 per side.
ledge=cube([102.4,102.4,2.5],[2.3,2.3,10])-cube([99.6,99.6,4],[3.7,3.7,9.5])
lid+=ledge
lid+=cube([103.4,103.4,1.2],[1.8,1.8,12])-cube([99.6,99.6,3],[3.7,3.7,11.5])
parts={}
report={"status":"CONCEPT_ONLY_NOT_FOR_FINAL_PRINT", "angle_deg":25,"outer_mm":[107,107,42],"pcb_origin_mm":[6,6,7],"unverified":["all module installed heights","OLED active area offset","encoder shaft offset","keycap centres and travel","terminal opening and wire bend","lid fasteners and retention","whole assembly collisions"]}
for name,solid in [('Base_CONCEPT',base),('Lid_CONCEPT',lid)]:
 raw=solid.to_mesh(); mesh=trimesh.Trimesh(vertices=raw.vert_properties[:,:3],faces=raw.tri_verts,process=True)
 parts[name]=mesh
 export=mesh.copy();export.apply_translation([0,0,-export.bounds[0,2]])
 path=OUT/(name+'.stl');export.export(path)
 check=trimesh.load(path,force='mesh')
 counts=np.bincount(check.edges_unique_inverse)
 parent=list(range(len(check.faces)))
 def find(a):
  while parent[a]!=a:
   parent[a]=parent[parent[a]];a=parent[a]
  return a
 for a,b in check.face_adjacency:parent[find(int(a))]=find(int(b))
 components=len({find(i) for i in range(len(parent))})
 metrics={'watertight':bool(check.is_watertight),'winding_consistent':bool(check.is_winding_consistent),'connected_components':components,'bad_edge_count':int(np.count_nonzero(counts!=2)),'volume_cm3':float(check.volume/1000),'extents_mm':check.extents.tolist()}
 assert metrics['watertight'] and metrics['winding_consistent'] and metrics['connected_components']==1 and metrics['bad_edge_count']==0,metrics
 report[name]=metrics
report['total_volume_cm3']=sum(m.volume/1000 for m in parts.values())
(OUT/'geometry_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
fig=plt.figure(figsize=(15,7),facecolor='#f0f3f6')
for i,exploded in enumerate([False,True]):
 ax=fig.add_subplot(1,2,i+1,projection='3d'); ax.set_facecolor('#f0f3f6')
 for name,mesh in parts.items():
  v=mesh.vertices.copy()
  if exploded and name.startswith('Lid'):v[:,2]+=30
  from matplotlib.colors import to_rgb
  light=np.array([-.4,-.5,1.]);light/=np.linalg.norm(light)
  shade=.62+.38*np.clip(mesh.face_normals@light,0,1)
  colors=shade[:,None]*np.array(to_rgb('#30485c' if name.startswith('Base') else '#b3cad8'))
  poly=Poly3DCollection(v[mesh.faces],facecolor=colors,edgecolor='none',alpha=1,zsort='average')
  ax.add_collection3d(poly)
 if exploded:
  pcb=trimesh.creation.box([95,95,1.6]);pcb.apply_translation([53.5,53.5,7.8]);ax.add_collection3d(Poly3DCollection(pcb.triangles,facecolor='#26836b',alpha=.65))
 ax.set_xlim(0,107);ax.set_ylim(0,107);ax.set_zlim(0,80);ax.set_box_aspect([107,107,80]);ax.view_init(elev=32,azim=48)
 ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
 ax.set_title('ASSEMBLED CONCEPT' if not exploded else 'EXPLODED / PCB ENVELOPE',fontsize=14)
fig.suptitle('SMART FAN / 25 DEGREE ENCLOSURE CONCEPT 01\nNOT FIT-CERTIFIED - DO NOT ORDER FINAL PRINT',fontsize=17,fontweight='bold')
plt.tight_layout();fig.savefig(OUT/'concept_preview.png',dpi=160);plt.close(fig)
(OUT/'README.md').write_text('''# 智能风扇外壳雏形 01

仅供外观和布局讨论，不能直接作为装配已验证的生产打印文件。

- 107×107mm平面外形，最高42mm，前侧25°斜面。壁厚名义2mm。
- 保持95×95mm母板，XY偏置6mm，四安装孔85mm孔距，板底Z7mm。PCB尺寸依据现有设计，安装高度为本雏形假设。
- 底座/顶盖两件。OLED移至后部水平区，不再用旧前面板孔位；按键有局部水平凸台；旋钮和手势窗口为待实物定位的占位孔。
- 后侧仅留电源线矩形出口，不冒称适配已购地博端子；不保留旧圆形DC口。
- 风扇头支架、舵机安装仓暂缓，不生成虚假的通用安装孔。
- 顶盖目前只有定位边，无最终锁盖螺丝/卡扣，不能把它当可靠固定结构。螺柱试孔为2.4mm设计值，需根据螺丝/材料试样再定。
- STL已各自落地Z=0，预览爆炸图则恢复装配坐标。网格检查与材料体积见geometry_check.json；水密不等于防水，不等于装配无干涉。
- 模块高度、按钮露出、屏面偏移、旋钮轴心、USB位置、线束弯曲空间尚未实测。当前窗口不代表最终孔径。25°形态保留，但孔位后续允许改变。
- 70cm³是此前材料预算目标，本版以实际报告数值为准，不为追预算削薄未知承重结构。

下一版：根据模块实物锁定开孔，补锁盖结构、通风与扬声器布局，进行元件包络干涉校核，然后才输出最终打印建议。
''',encoding='utf-8')
with zipfile.ZipFile(OUT/'SmartFan_Enclosure_Concept01.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['Base_CONCEPT.stl','Lid_CONCEPT.stl','concept_preview.png','geometry_check.json','README.md']:z.write(OUT/name,name)
 z.write(Path(__file__),'build_enclosure_concept_20261109.py')
print(json.dumps(report,indent=2))
print(OUT)
