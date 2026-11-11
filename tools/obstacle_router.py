"""Two-layer obstacle A* router. NC pads are obstacles; GND is explicitly routed.
Fails closed instead of publishing partial copper. Units: millimetres.
"""
import heapq, json, math
from pathlib import Path
import numpy as np
from shapely.geometry import Point, LineString, box
from shapely import intersects_xy
STEP=.1
CLEARANCE=.25
GUARD=.055
VIA_SIZE=.6
VIA_DRILL=.3
LAYERS=('F.Cu','B.Cu')
HOLE_CLEARANCE=.25
PAD_MASK_EXPANSION=.05
VIA_DRILL_MASK_CLEARANCE=.10
VIA_CENTER_PAD_CLEARANCE=PAD_MASK_EXPANSION+VIA_DRILL/2+VIA_DRILL_MASK_CLEARANCE

class DrillRegistry:
    """Mechanical holes are obstacles even when their copper belongs to one net.

    Only an existing via at exactly the same coordinate and net may be reused.
    Pad records store THT/hole drill diameter in h (not the copper diameter w).
    """
    def __init__(self, pads):
        self.holes=[(p['x'],p['y'],p['h'],None) for p in pads
                    if p['type'] in ('tht','hole')]
        self.vias={}
        self.pads=tuple(dict(p) for p in pads)

    def can_place(self, x, y, net):
        for p in self.pads:
            dx=abs(x-p['x']);dy=abs(y-p['y'])
            if p['type']=='smd':
                distance=math.hypot(max(0.,dx-p['w']/2),max(0.,dy-p['h']/2))
            else:
                distance=max(0.,math.hypot(dx,dy)-p['w']/2)
            if distance<VIA_CENTER_PAD_CLEARANCE-1e-9:return False
        for hx,hy,diameter,owner in self.holes:
            if owner==net and (x,y)==(hx,hy):
                continue
            if math.hypot(x-hx,y-hy)-(VIA_DRILL+diameter)/2 < HOLE_CLEARANCE-1e-9:
                return False
        return True

    def add(self, x, y, net):
        if not self.can_place(x,y,net):
            raise ValueError(f'Via drill clearance violation at {(x,y)} net {net}')
        key=(x,y)
        if key in self.vias:
            if self.vias[key]!=net:
                raise ValueError('Cannot reuse a different-net via')
            return False
        self.vias[key]=net
        self.holes.append((x,y,VIA_DRILL,net))
        return True

    def first_conflict(self, points, net):
        """Validate all transitions transactionally, including within one A* path."""
        trial=DrillRegistry([])
        trial.holes=self.holes.copy()
        trial.vias=self.vias.copy()
        trial.pads=self.pads
        for x,y in points:
            if not trial.can_place(x,y,net):
                return (x,y)
            trial.add(x,y,net)
        return None

def pad_geometry(p):
    x,y,w,h=p['x'],p['y'],p['w'],p['h']
    return box(x-w/2,y-h/2,x+w/2,y+h/2) if p['type']=='smd' else Point(x,y).buffer(w/2,quad_segs=128)
POWER_WIDTHS = {'+5V_RAW':2.0, '+5V_FUSED':2.0, '+5V':2.0,
                'GND':2.0, 'TB_AO1':1.0, 'TB_AO2':1.0,
                '+5V_ASR':1.0}
POWER_REFS = {'DC1','F1','Q_PWR','SERVO1','J_TB_R','MOTO1','C1','C3','C_VM'}

def power_terminals(pads, net_names):
    """Terminal policy separates load paths from low-current same-net branches."""
    groups={}
    for p in pads:
        name=net_names.get(p['nid'])
        if name not in POWER_WIDTHS:continue
        selected=(name in ('+5V_RAW','+5V_FUSED','TB_AO1','TB_AO2','+5V_ASR') or
                  p['ref'] in POWER_REFS or 'ASR' in p['ref'])
        # Q_PWR gate is only a bias return, not a load-current return terminal.
        if p['ref']=='Q_PWR' and name=='GND':selected=False
        if selected:groups.setdefault(p['nid'],[]).append(p)
    return {n:ps for n,ps in groups.items() if len(ps)>1}

def route_power_backbone(pads, net_names, bounds):
    """Fixed-layer power copper (GND back, others front), no added power vias.
    Existing >=0.8mm plated THT terminals bridge the back-layer return;
    their hole-wall current capability remains unverified.

    SO8 source/drain pins each get a <=2 mm, >=.50 mm escape, individually
    connected to the wide tree. Other power terminals may escape at 1 mm.
    Main/return trunks are 2 mm; motor/isolated ASR trunks 1 mm. No current
    sharing or 2 A thermal rating is claimed for the package, connectors or PCB.
    """
    groups=power_terminals(pads,net_names)
    ports={};escapes=[];records=[]
    ox,oy,xmax,ymax=bounds
    board=box(ox+.30,oy+.30,xmax-.30,ymax-.30)
    obstacles=[(p['nid'],(0,) if p['type']=='smd' else (0,1),pad_geometry(p)) for p in pads]
    for n,terminals in groups.items():
        width=POWER_WIDTHS[net_names[n]];ports[n]=[]
        layer=1 if net_names[n]=='GND' else 0
        for p in terminals:
            if layer==1 and (p['type']!='tht' or p['h']<.8):
                raise RuntimeError('Back-layer power return requires existing >=0.8mm plated THT: '+p['ref'])
            ew=.5 if p['ref']=='Q_PWR' else min(1.,width)
            foreign=[g for other,ls,g in obstacles if other!=n and layer in ls]
            candidates=[]
            gx=round((p['x']-ox)/STEP);gy=round((p['y']-oy)/STEP)
            for dx in range(-20,21):
                for dy in range(-20,21):
                    x=ox+(gx+dx)*STEP;y=oy+(gy+dy)*STEP
                    length=math.hypot(x-p['x'],y-p['y'])
                    if length<=2.+1e-9:candidates.append((length,x,y))
            chosen=None
            for length,x,y in sorted(candidates):
                landing=Point(x,y).buffer(width/2,quad_segs=64)
                escape=LineString([(p['x'],p['y']),(x,y)]).buffer(ew/2,quad_segs=64)
                copper=landing.union(escape)
                if not board.covers(copper):continue
                if any(copper.distance(g)<CLEARANCE+GUARD+.01 for g in foreign):continue
                chosen=(x,y,length);break
            if chosen is None:
                raise RuntimeError(f'No <=2mm power escape for {p["ref"]}.{p["pad"]}; placement change required')
            x,y,length=chosen
            port=dict(p,x=x,y=y,type='smd',route_layer=layer)
            ports[n].append(port)
            obstacles.append((n,(layer,),Point(x,y).buffer(width/2,quad_segs=64)))
            if length>1e-9:
                tr=(p['x'],p['y'],x,y,ew,LAYERS[layer],n)
                escapes.append(tr)
                obstacles.append((n,(layer,),LineString([(p['x'],p['y']),(x,y)]).buffer(ew/2,quad_segs=64)))
            records.append(dict(ref=p['ref'],pad=p['pad'],net=net_names[n],
                                terminal=[p['x'],p['y']],port=[x,y],
                                escape_width_mm=ew,escape_length_mm=length))
    tracks,vias=route_board(pads,bounds,route_groups=ports,
                           width_overrides={n:POWER_WIDTHS[net_names[n]] for n in ports},
                           front_only=True,initial_tracks=escapes,
                           reserved_copper=[(n,(p['route_layer'],),Point(p['x'],p['y']).buffer(POWER_WIDTHS[net_names[n]]/2,quad_segs=64))
                                            for n,ps in ports.items() for p in ps])
    assert not vias,'Power backbone must not depend on any via'
    return tracks,dict(design_target_a=2.,thermal_certified=False,
                       widths_mm=POWER_WIDTHS,layers_by_net={name:('B.Cu' if name=='GND' else 'F.Cu') for name in POWER_WIDTHS},via_count=0,
                       max_escape_length_mm=2.,terminals=records,
                       limitations=['2A is a design target, not thermal certification.',
                                    'SO8 parallel-pin current sharing, connector ratings, copper thickness, startup/stall and temperature rise require validation.',
                                    'Default .3mm vias may serve low-current branches only; the independent wide-tree path never uses them.'])

def route_board(pads,bounds=(100.,100.,195.,195.),report_path=None, *,
                route_groups=None, width_overrides=None, front_only=False,
                initial_tracks=(), net_names=None, reserved_copper=()):
    if net_names is not None:
        power_tracks, power_report = route_power_backbone(pads, net_names, bounds)
        tracks, vias = route_board(pads, bounds, report_path,
                                  initial_tracks=power_tracks,
                                  width_overrides={n:.5 for n,name in net_names.items()
                                                   if name in ('GND','+5V_RAW','+5V_FUSED','+5V','+5V_MCU','+3.3V')})
        from verify_revb_power import audit_power
        power_audit=audit_power(pads,tracks,vias,net_names,power_report)
        if not power_audit['passed']:
            raise RuntimeError('Power routing audit failed: '+str(power_audit['errors']))
        power_report['independent_audit']=power_audit
        power_report['thermal_certified'] = False
        if report_path:
            path=Path(report_path)
            report=json.loads(path.read_text(encoding='utf-8'))
            report['power_rules']=power_report
            path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        return tracks,vias
    ox,oy,xmax,ymax=bounds
    nx=int(round((xmax-ox)/STEP))+1;ny=int(round((ymax-oy)/STEP))+1;plane=nx*ny
    geometries=[(p['nid'],(0,) if p['type']=='smd' else (0,1),pad_geometry(p)) for p in pads]
    geometries.extend(reserved_copper)
    groups=route_groups if route_groups is not None else {n:[p for p in pads if p['nid']==n] for n in sorted({p['nid'] for p in pads if p['nid']})}
    widths={n:(.5 if n in (1,2,3,4,5,6,13,14,18,21,22) else .25) for n in groups}
    widths.update(width_overrides or {})
    def coord(k):
        l,r=divmod(int(k),plane);y,x=divmod(r,nx)
        return (ox+x*STEP,oy+y*STEP,l)
    def nodes(p):
        x=round((p['x']-ox)/STEP);y=round((p['y']-oy)/STEP)
        layers=(p.get('route_layer',0),) if front_only else ((0,) if p['type']=='smd' else (0,1))
        return [l*plane+y*nx+x for l in layers]
    def paint(mask,g,layers,radius):
        g=g.buffer(radius,quad_segs=32);a,b,c,d=g.bounds
        x0=max(0,math.floor((a-ox)/STEP));x1=min(nx-1,math.ceil((c-ox)/STEP))
        y0=max(0,math.floor((b-oy)/STEP));y1=min(ny-1,math.ceil((d-oy)/STEP))
        if x0>x1 or y0>y1:return
        xs=ox+np.arange(x0,x1+1)*STEP;ys=oy+np.arange(y0,y1+1)*STEP
        hit=intersects_xy(g,xs[None,:],ys[:,None])
        for l in layers:mask[l,y0:y1+1,x0:x1+1]|=hit
    def masks(n,obstacles):
        w=widths[n];blocked=np.zeros((2,ny,nx),dtype=bool);vb=blocked.copy()
        edge=int(math.ceil((.3+max(w/2,VIA_SIZE/2))/STEP))
        for m in (blocked,vb):
            m[:,:edge,:]=True;m[:,-edge:,:]=True;m[:,:,:edge]=True;m[:,:,-edge:]=True
        for other,ls,g in obstacles:
            if other==n:continue
            paint(blocked,g,ls,w/2+CLEARANCE+GUARD)
            paint(vb,g,ls,VIA_SIZE/2+CLEARANCE+GUARD)
        return blocked.ravel(),(vb[0]|vb[1]).ravel()
    def drill_mask(n,copper_mask,drills):
        copper_vb=copper_mask.reshape(ny,nx)
        vb=np.broadcast_to(copper_vb,(2,ny,nx)).copy()
        for p in drills.pads:
            paint(vb,pad_geometry(p),(0,1),VIA_CENTER_PAD_CLEARANCE+.001)
        for x,y,d,owner in drills.holes:
            # Small raster guard compensates polygon chord approximation only.
            paint(vb,Point(x,y),(0,1),(d+VIA_DRILL)/2+HOLE_CLEARANCE+.001)
        for (x,y),owner in drills.vias.items():
            if owner!=n:continue
            ix=round((x-ox)/STEP);iy=round((y-oy)/STEP)
            if 0<=ix<nx and 0<=iy<ny and not copper_vb[iy,ix] and drills.can_place(x,y,n):
                vb[:,iy,ix]=False
        return (vb[0]|vb[1]).ravel()
    def astar(starts,goals,blocked,vb):
        goals=set(goals);target=[coord(k) for k in goals]
        def h(k):
            x,y,l=coord(k)
            return min((abs(x-a)+abs(y-b))/STEP+(0 if l==z else 10) for a,b,z in target)
        q=[];dist={};prev={}
        for s in starts:
            if not blocked[s]:dist[s]=0;heapq.heappush(q,(h(s),0,s))
        while q:
            _,negcost,k=heapq.heappop(q)
            cost=-negcost
            if cost!=dist[k]:continue
            if k in goals:
                path=[k]
                while k in prev:k=prev[k];path.append(k)
                return path[::-1]
            l,r=divmod(k,plane);y,x=divmod(r,nx);candidates=[]
            if x>0:candidates.append((k-1,1.0))
            if x+1<nx:candidates.append((k+1,1.0))
            if y>0:candidates.append((k-nx,1.0))
            if y+1<ny:candidates.append((k+nx,1.0))
            if not vb[r]:candidates.append((k+plane if l==0 else k-plane,10.0))
            for t,dc in candidates:
                if blocked[t]:continue
                nc=cost+dc
                if nc<dist.get(t,float('inf')):
                    dist[t]=nc;prev[t]=k;heapq.heappush(q,(nc+h(t),-nc,t))
        return None
    order=sorted(groups,key=lambda n:(n==1,n not in (6,2,3,4,5,13,14),-len(groups[n]),n))
    failures=[];seen_orders=set()
    import random
    rng=random.Random(20261104)
    for attempt in range(32 if front_only else 12):
        if tuple(order) in seen_orders:
            for _ in range(100):
                rng.shuffle(order)
                if tuple(order) not in seen_orders:break
        seen_orders.add(tuple(order))
        obstacles=geometries[:];tracks=list(initial_tracks);vias=[];failed=None;drills=DrillRegistry(pads)
        for x1,y1,x2,y2,w,l,nid in initial_tracks:
            obstacles.append((nid,(LAYERS.index(l),),LineString([(x1,y1),(x2,y2)]).buffer(w/2,quad_segs=32)))
        print('Router attempt',attempt+1,'order',order,flush=True)
        for n in order:
            blocked,copper_vb=masks(n,obstacles)
            pp=groups[n];connected=[pp[0]];pending=pp[1:];w=widths[n];nt=[];nv=[]
            while pending:
                vb=drill_mask(n,copper_vb,drills)
                if front_only:vb[:]=True
                _,i,j=min((math.hypot(a['x']-b['x'],a['y']-b['y']),i,j) for i,a in enumerate(connected) for j,b in enumerate(pending))
                a,b=connected[i],pending[j]
                while True:
                    path=astar(nodes(a),nodes(b),blocked,vb)
                    if path is None:break
                    pts=[coord(k) for k in path]
                    transitions=[u[:2] for u,v in zip(pts,pts[1:]) if u[2]!=v[2]]
                    conflict=drills.first_conflict(transitions,n)
                    if conflict is None:break
                    # Do not delete a transition: forbid it and reroute the entire path.
                    x,y=conflict
                    vb[round((y-oy)/STEP)*nx+round((x-ox)/STEP)]=True
                if path is None:
                    failed=n;failures.append(dict(attempt=attempt+1,net=n,source=f"{a['ref']}.{a['pad']}",target=f"{b['ref']}.{b['pad']}",source_xy=[a['x'],a['y']],target_xy=[b['x'],b['y']],source_blocked=all(bool(blocked[k]) for k in nodes(a)),target_blocked=all(bool(blocked[k]) for k in nodes(b))));break
                pts=[coord(k) for k in path]
                pts=[(a['x'],a['y'],pts[0][2])]+pts+[(b['x'],b['y'],pts[-1][2])];compact=[pts[0]]
                for p in pts[1:]:
                    if p==compact[-1]:continue
                    if len(compact)>1:
                        u,v=compact[-2:]
                        if u[2]==v[2]==p[2] and abs((v[0]-u[0])*(p[1]-v[1])-(v[1]-u[1])*(p[0]-v[0]))<1e-9:
                            compact[-1]=p;continue
                    compact.append(p)
                for u,v in zip(compact,compact[1:]):
                    if u[2]!=v[2]:
                        if drills.add(u[0],u[1],n):nv.append((u[0],u[1],VIA_SIZE,VIA_DRILL,n))
                    elif u[:2]!=v[:2]:nt.append((*u[:2],*v[:2],w,LAYERS[u[2]],n))
                connected.append(pending.pop(j))
            if failed is not None:break
            for x1,y1,x2,y2,w,l,nid in nt:obstacles.append((nid,(LAYERS.index(l),),LineString([(x1,y1),(x2,y2)]).buffer(w/2,quad_segs=32)))
            for x,y,s,d,nid in nv:obstacles.append((nid,(0,1),Point(x,y).buffer(s/2,quad_segs=64)))
            tracks+=nt;vias+=nv
            print('  net',n,'pads',len(pp),'segments',len(nt),'vias',len(nv),flush=True)
        if failed is None:
            report=dict(status='routed',grid_mm=STEP,clearance_mm=CLEARANCE,hole_clearance_mm=HOLE_CLEARANCE,via_drill_to_pad_mask_clearance_mm=VIA_DRILL_MASK_CLEARANCE,pad_mask_expansion_mm=PAD_MASK_EXPANSION,via_center_to_pad_copper_mm=VIA_CENTER_PAD_CLEARANCE,unique_vias=True,guard_mm=GUARD,net_count=len(groups),pad_count=sum(map(len,groups.values())),tracks=len(tracks),vias=len(vias),attempts=attempt+1,prior_failures=failures,widths_mm=widths)
            if report_path:Path(report_path).write_text(json.dumps(report,indent=2),encoding='utf-8')
            return tracks,vias
        print('  FAILED',failures[-1],flush=True);order.remove(failed);order.insert(0,failed)
    if report_path:Path(report_path).write_text(json.dumps(dict(status='failed',failures=failures),indent=2),encoding='utf-8')
    raise RuntimeError('Obstacle routing incomplete; no board emitted: '+str(failures[-1]))
