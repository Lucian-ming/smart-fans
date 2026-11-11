"""Independent wide-tree power gate. Geometry acceptance is NOT a 2 A rating."""
import argparse
import json
import math
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from verify_revb_connectivity import check_networks

# Deliberately repeated here: audit policy must not inherit router's implementation.
WIDTHS={'+5V_RAW':2.,'+5V_FUSED':2.,'+5V':2.,'GND':2.,'TB_AO1':1.,'TB_AO2':1.,'+5V_ASR':1.}
REFS={'DC1','F1','Q_PWR','SERVO1','J_TB_R','MOTO1','C1','C3','C_VM'}

def audit_power(pads,tracks,vias,net_names,power_report):
    groups={};errors=[]
    for p in pads:
        name=net_names.get(p['nid'])
        if name not in WIDTHS:continue
        selected=name in ('+5V_RAW','+5V_FUSED','TB_AO1','TB_AO2','+5V_ASR') or p['ref'] in REFS or 'ASR' in p['ref']
        if p['ref']=='Q_PWR' and name=='GND':selected=False
        if selected:groups.setdefault(p['nid'],[]).append(p)
    groups={n:ps for n,ps in groups.items() if len(ps)>1}
    records=power_report.get('terminals',[])
    for n,ps in groups.items():
        name=net_names[n];width=WIDTHS[name];conductors=[];ap=[]
        layer='B.Cu' if name=='GND' else 'F.Cu'
        wide=[t for t in tracks if t[6]==n and t[5]==layer and t[4]>=width-1e-9]
        wide_geom=unary_union([LineString([(t[0],t[1]),(t[2],t[3])]).buffer(t[4]/2) for t in wide])
        for i,t in enumerate(wide):
            conductors.append((f'wide{i}',n,layer,LineString([(t[0],t[1]),(t[2],t[3])]).buffer(t[4]/2)))
        for i,p in enumerate(ps):
            identity=f'{p["ref"]}.{p["pad"]}.{i}'
            if layer=='B.Cu' and (p['type']!='tht' or p['h']<.8):
                errors.append(identity+': missing >=0.8mm plated THT return bridge');continue
            layers=['F.Cu','B.Cu'] if p['type']=='tht' else ['F.Cu']
            ap.append(dict(id=identity,net=n,layers=layers))
            g=box(p['x']-p['w']/2,p['y']-p['h']/2,p['x']+p['w']/2,p['y']+p['h']/2) if p['type']=='smd' else Point(p['x'],p['y']).buffer(p['w']/2)
            conductors.extend((identity,n,l,g) for l in layers)
            rs=[r for r in records if r['ref']==p['ref'] and r['pad']==p['pad'] and r['net']==name and math.dist(r['terminal'],[p['x'],p['y']])<1e-6]
            if len(rs)!=1:errors.append(identity+': missing/duplicate power terminal record');continue
            r=rs[0];port=r['port'];length=math.dist(port,[p['x'],p['y']]);minimum=.5 if p['ref']=='Q_PWR' else min(1.,width)
            if length>2.+1e-6:errors.append(identity+': escape longer than 2mm')
            if wide_geom.is_empty or wide_geom.distance(Point(*port))>1e-6:errors.append(identity+': escape does not reach assigned-layer wide copper')
            if length<1e-9:continue
            matches=[t for t in tracks if t[6]==n and t[5]==layer and t[4]>=minimum-1e-9 and
                     ((math.dist(t[:2],[p['x'],p['y']])<1e-6 and math.dist(t[2:4],port)<1e-6) or
                      (math.dist(t[2:4],[p['x'],p['y']])<1e-6 and math.dist(t[:2],port)<1e-6))]
            if not matches:errors.append(identity+': missing adequately sized short escape');continue
            t=matches[0]
            conductors.append(('escape'+identity,n,layer,LineString([(t[0],t[1]),(t[2],t[3])]).buffer(t[4]/2)))
        result=check_networks(ap,conductors,{})
        if result['disconnected_net_count']:errors.append(name+': wide-only tree disconnected (ordinary thin tracks/vias excluded)')
    all_conductors=[]
    for i,p in enumerate(pads):
        g=box(p['x']-p['w']/2,p['y']-p['h']/2,p['x']+p['w']/2,p['y']+p['h']/2) if p['type']=='smd' else Point(p['x'],p['y']).buffer(p['w']/2)
        for layer in (['F.Cu'] if p['type']=='smd' else ['F.Cu','B.Cu']):all_conductors.append((f'pad{i}',p['nid'],layer,g))
    for i,t in enumerate(tracks):all_conductors.append((f'track{i}',t[6],t[5],LineString([t[:2],t[2:4]]).buffer(t[4]/2)))
    for i,v in enumerate(vias):
        for layer in ['F.Cu','B.Cu']:all_conductors.append((f'via{i}',v[4],layer,Point(v[0],v[1]).buffer(v[2]/2)))
    copper=check_networks([],all_conductors,{})
    if copper['clearance_violation_count']:errors.append('Actual copper clearance violations: '+str(copper['clearance_violation_count']))
    if not groups:errors.append('No recognized power paths; missing net names or terminal policy')
    return dict(passed=not errors,errors=errors,checked_nets=[net_names[n] for n in groups],
                design_target_a=2.,thermal_certified=False,via_current_assumed_a=0.,
                note='Assigned-layer wide trees only: GND on back through existing >=0.8mm plated THT, others front. Thermal, hole-wall current, startup/stall, pin sharing and connector capability unverified.')

def read_board(path):
    import sexpdata
    root=sexpdata.loads(path.read_text(encoding='utf8'))
    def rows(node,key):return [r for r in node if isinstance(r,list) and r and str(r[0])==key]
    def one(node,key):return rows(node,key)[0]
    pads=[];tracks=[];vias=[]
    for fp in rows(root,'footprint'):
        at=one(fp,'at');fx,fy=map(float,at[1:3]);angle=float(at[3]) if len(at)>3 else 0.
        if abs(angle)>1e-9:raise ValueError('Power reader requires unrotated instances; fail closed')
        refs=[r[2] for r in rows(fp,'property') if r[1]=='Reference']
        if not refs:refs=[r[2] for r in rows(fp,'fp_text') if str(r[1])=='reference']
        if len(refs)!=1:raise ValueError('Missing/duplicate Reference')
        for p in rows(fp,'pad'):
            at=one(p,'at');size=one(p,'size');x,y=map(float,at[1:3]);w,h=map(float,size[1:3])
            angle=float(at[3]) if len(at)>3 else 0.
            if abs(angle%90)>1e-9:raise ValueError('Nonorthogonal pad unsupported; fail closed')
            if int(round(angle/90))%2:w,h=h,w
            nets=rows(p,'net');nid=int(nets[0][1]) if nets else 0
            typ='smd' if str(p[2])=='smd' else ('tht' if str(p[2])=='thru_hole' else 'hole')
            if typ!='smd':h=float(one(p,'drill')[1])
            pads.append(dict(ref=str(refs[0]),pad=str(p[1]),nid=nid,x=fx+x,y=fy+y,w=w,h=h,type=typ))
    for s in rows(root,'segment'):
        tracks.append((*map(float,one(s,'start')[1:3]),*map(float,one(s,'end')[1:3]),float(one(s,'width')[1]),str(one(s,'layer')[1]),int(one(s,'net')[1])))
    for v in rows(root,'via'):
        vias.append((*map(float,one(v,'at')[1:3]),float(one(v,'size')[1]),float(one(v,'drill')[1]),int(one(v,'net')[1])))
    return pads,tracks,vias,{int(n[1]):str(n[2]) for n in rows(root,'net')}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Audit router JSON fixture/final captured route data')
    ap.add_argument('input',type=Path,nargs='?',help='JSON keys pads,tracks,vias,net_names,power_rules')
    ap.add_argument('--pcb',type=Path)
    ap.add_argument('--router-report',type=Path)
    ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    if args.pcb:
        if args.input or not args.router_report:ap.error('--pcb requires --router-report and excludes input')
        pads,tracks,vias,names=read_board(args.pcb)
        report=json.loads(args.router_report.read_text(encoding='utf8'))
        result=audit_power(pads,tracks,vias,names,report.get('power_rules',{}))
    else:
        if not args.input:ap.error('Provide input JSON or --pcb with --router-report')
        data=json.loads(args.input.read_text(encoding='utf8'))
        result=audit_power(data['pads'],data['tracks'],data['vias'],{int(k):v for k,v in data['net_names'].items()},data['power_rules'])
    if args.report:args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
