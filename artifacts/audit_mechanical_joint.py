import ast,json,math,hashlib
from pathlib import Path
import numpy as np
import trimesh,sexpdata
R=Path(__file__).resolve().parents[1]
p=R/'tools/build_perfect_revB_v3.py'
t=ast.parse(p.read_text(encoding='utf-8-sig'))
cs=next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='COMPONENTS' for a in n.targets))
def tag(a,k): return next((b for b in a if isinstance(b,list) and b and str(b[0])==k),None)
pcb=sexpdata.loads((R/'hardware/kicad/fan_ctrl_revB.kicad_pcb').read_text(encoding='utf-8'))
actual={}
for f in pcb:
 if not isinstance(f,list) or not f or str(f[0])!='footprint':continue
 ref=next((v[2] for v in f if isinstance(v,list) and len(v)>2 and str(v[0])=='property' and str(v[1])=='Reference'),None)
 if ref is None: continue
 a=tag(f,'at');actual[str(ref)]={'xy':[float(a[1])-98,float(a[2])-98], 'pads':[]}
 for v in f:
  if isinstance(v,list) and v and str(v[0])=='pad':
   q=tag(v,'at');net=tag(v,'net');actual[str(ref)]['pads'].append({'pin':v[1],'xy':[float(a[1])+float(q[1])-98,float(a[2])+float(q[2])-98],'net':str(net[2]) if net else 'NC'})
assert len(actual)==47, len(actual)
assert all(np.allclose(actual[c['ref']]['xy'],[c['x']+2,c['y']+2]) for c in cs)
parts={}
meshes={}
for n in ['SmartFan_Piece1_Base_Enclosure','SmartFan_Piece3_Removable_Lid','SmartFan_Piece2_Fan_Gimbal_Bracket']:
 f=R/'mechanical/stl/print'/f'{n}.stl';m=trimesh.load_mesh(f);meshes[n]=m
 parts[n]={'bounds':m.bounds.tolist(),'volume_cm3':m.volume/1000,'watertight':bool(m.is_watertight),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
lid=meshes['SmartFan_Piece3_Removable_Lid']
def hits(x,y):
 loc,_,_=lid.ray.intersects_location([[x,y,-1]],[[0,0,1]])
 return sorted(set(round(float(z),6) for z in np.asarray(loc).reshape(-1,3)[:,2]))
probes={k:{'xy':xy,'lid_z_hits':hits(*xy)} for k,xy in {'mcu_front_corner':[60.9,68.65],'mcu_rear':[49.5,15.35],'mcu_servo_axis':[49.5,35],'gesture_socket':[18,76],'oled_socket':[80.5,57],'ec11_socket':[73,84.5],'button_socket':[36,84.5],'dht_socket':[17.5,57],'voice_centre':[80.5,27.5]}.items()}
g=meshes['SmartFan_Piece2_Fan_Gimbal_Bracket'];v=g.vertices.copy();v[:,:2]-=[42,15]
r=np.linalg.norm(v[:,:2],axis=1).max()
report={'method':'Read actual PCB and STL only. Envelope numbers below explicitly conditional, no CAD generator imports.','parts':parts,'actual_connectors':{k:v for k,v in actual.items() if k.startswith('J_') or k in ['DC1','SPK1','MIC1','SERVO1','MOTO1']},'lid_probes':probes,'bluepill_centered_nominal_envelope':{'xy_bounds':[[38.1,15.35],[60.9,68.65]],'assumption':'53.3Y x22.8X centered on two socket rows; real PCB-to-pin datums unmeasured','rear_edge_to_inner_rear_wall':15.35-1.6,'servo_slot_projected_overlap':'23.2x12.6 slot overlaps essentially full MCU width; physical servo body/axis datum not supplied'},'gimbal':{'pivot_assumed_local':[42,15],'full_rotation_printed_mesh_max_radius':float(r),'axis_if_case_slot_center':[49.5,35],'full_turn_xy_bounds_if_axis_slot_center':[[49.5-r,35-r],[49.5+r,35+r]],'unknowns':['real output shaft offset relative servo case','gimbal assembled Z','motor/propeller and wire envelopes','safe angular range and feedback']},'assembly_release':False}
out=R/'artifacts/mechanical_joint_review_data.json';out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(report,indent=2,ensure_ascii=False))
