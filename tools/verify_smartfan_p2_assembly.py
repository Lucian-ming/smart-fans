"""Independent three-part audit: only exported STL, never CAD constants/functions."""
from verify_smartfan_mechanical import *
from manifold3d import Manifold, Mesh


def plane_openings(mesh, n, d):
    mask=(mesh.face_normals@n>.99)&(np.max(abs(mesh.triangles@n-d),axis=1)<2e-5)
    tangent=np.cross(n,[1.,0.,0.]); tangent/=np.linalg.norm(tangent)
    loops=boundary_loops(mesh,mask)
    loops.sort(key=lambda p:polygon_area(np.column_stack([p[:,0],p@tangent])),reverse=True)
    return [dict(center_xyz_mm=((p.min(axis=0)+p.max(axis=0))/2).tolist(),
                 size_surface_mm=np.ptp(np.column_stack([p[:,0],p@tangent]),axis=0).tolist(),
                 points=p,uv=np.column_stack([p[:,0],p@tangent])) for p in loops[1:]]


def to_solid(mesh):
    return Manifold(Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))


def overlap(mesh,other):
    solid=to_solid(mesh)
    return float((solid-(solid-other)).volume())


def section_image(base,lid):
    from PIL import Image,ImageDraw
    image=Image.new('RGB',(1400,900),'white'); draw=ImageDraw.Draw(image)
    draw.text((30,20),'P2 INDEPENDENT STL SECTIONS - blue: lower / green: lid / orange: assumed bare PCB',fill='black')
    def panel(x,ymin,ymax,zmin,zmax,ox,oy,scale,title):
        def pos(y,z): return (int(ox+(y-ymin)*scale),int(oy+(zmax-z)*scale))
        draw.text((ox,oy-25),title,fill='black')
        for mesh,color in [(base,'#2563eb'),(lid,'#15803d')]:
            for tri in mesh.triangles:
                points=[]
                for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                    if (a[0]-x)*(b[0]-x)<0:
                        t=(x-a[0])/(b[0]-a[0]); points.append(a+t*(b-a))
                if len(points)==2 and all(ymin<=p[1]<=ymax and zmin<=p[2]<=zmax for p in points):
                    draw.line([pos(p[1],p[2]) for p in points],fill=color,width=2)
        for z in [6.5,8.1]: draw.line([pos(max(2,ymin),z),pos(min(97,ymax),z)],fill='#d97706',width=2)
        if x==36:
            draw.line([pos(86,8.1),pos(86,23.1)],fill='#be185d',width=3)
            draw.text(pos(55,29),'ASSUMED module bottom Z8.1 + H15 -> top Z23.1',fill='#be185d')
            draw.text(pos(55,26),'Face centre Z21.75; conditional vertical protrusion 1.35',fill='#be185d')
        draw.text((ox,oy+(zmax-zmin)*scale+10),'Y increases right; Z increases up. Lines are triangle/plane intersections.',fill='black')
    panel(36,0,99,0,35,50,85,12,'SECTION X36: removable lid, button pedestal, bare-PCB datum')
    panel(92,80,99,6,22,50,595,14,'SECTION X92: front-right M2.5 seat near MIC bore (zoom)')
    draw.text((450,630),'M2.5 front L12 / rear L30; head diameter <=4.5mm, no large washer.',fill='black')
    draw.text((450,665),'Module/body/shaft/travel absent: magenta line is NOT a real button model.',fill='black')
    draw.text((450,700),'Bare-board fit only. Component envelopes and strength require assembly verification.',fill='black')
    out=ROOT/'mechanical/P2_mechanical_sections.png'; image.save(out); return str(out.relative_to(ROOT))


def main():
    base,b=audit_mesh(FOLDER/'SmartFan_Piece1_Base_Enclosure.stl')
    lid,l=audit_mesh(FOLDER/'SmartFan_Piece3_Removable_Lid.stl')
    _,g=audit_mesh(FOLDER/'SmartFan_Piece2_Fan_Gimbal_Bracket.stl')
    normals=lid.face_normals
    candidates=np.where((normals[:,2]>.8)&(normals[:,1]>.3)&(abs(normals[:,0])<.01))[0]
    idx=candidates[np.argmax(lid.area_faces[candidates])]
    n=normals[idx]; d=float(lid.triangles_center[idx]@n)
    openings=plane_openings(lid,n,d); labelled={}
    for name,xy in [('OLED',(80.5,64)),('EC11',(73,88)),('PAJ7620',(18,76)),('MIC',(92,88))]:
        hole=min(openings,key=lambda o:np.linalg.norm(np.array(o['center_xyz_mm'][:2])-xy))
        assert np.linalg.norm(np.array(hole['center_xyz_mm'][:2])-xy)<.01
        labelled[name]=hole
    buttons={}
    for name,x in [('KEY1',36),('KEY2',51.5)]:
        local=candidates[abs(lid.triangles_center[candidates,0]-x)<5.9]
        local_d=float(np.max(lid.triangles_center[local]@n))
        holes=[o for o in plane_openings(lid,n,local_d) if np.linalg.norm(np.array(o['center_xyz_mm'][:2])-[x,86])<.01]
        hole=min(holes,key=lambda o:polygon_area(o['uv']))
        assert np.linalg.norm(np.array(hole['center_xyz_mm'][:2])-[x,86])<.01
        labelled[name]=hole; z=hole['center_xyz_mm'][2]
        buttons[name]=dict(measured_panel_center_xyz_mm=hole['center_xyz_mm'],measured_surface_bore_size_mm=hole['size_surface_mm'],
            assumed_module_bottom_z_mm=8.1,user_supplied_module_bottom_to_cap_top_mm=15,
            assumed_axis='vertical Z; cap top compared to surface at centre, not normal offset',
            conditional_cap_top_z_mm=23.1,conditional_vertical_protrusion_mm=23.1-z,actual_protrusion_mm=None,
            status='CONDITIONAL ONLY: module PCB bottom must be at Z8.1; real body/cap/axis/travel absent')
    p=labelled['OLED']['uv']; q=labelled['EC11']['uv']
    gap=min(point_segment_min(p,q),point_segment_min(q,p))
    inner=(normals@n<-.999999)&(lid.area_faces>1)
    panel_thickness=float(d-np.median(lid.triangles_center[inner]@n))
    top_hits=vertical_hits(lid,20.123,30.321); bottom_hits=vertical_hits(base,20.123,30.321)
    boss_hits=vertical_hits(base,9.25,7.123)
    inner_x=[]
    for sign in [1,-1]:
        ids=(base.face_normals[:,0]*sign>.999)&(base.area_faces>20)
        vals=base.triangles_center[ids,0]; inner_x.append(float(np.min(vals) if sign==1 else np.max(vals)))
    board=Manifold.cube([95,95,1.6]).translate([2,2,6.5])
    sweep=Manifold.cube([95,95,80]).translate([2,2,6.5])
    bv=overlap(base,board); lv=overlap(lid,board); iv=overlap(base,sweep); seam=overlap(base,to_solid(lid))
    screws=[]
    for x,y in [(7,7),(92,7),(7,92),(92,92)]:
        lh=vertical_hits(lid,x+1.8,y+.123); bh=vertical_hits(base,x+1.5,y+.123)
        seat=lh[-1]; length=30 if y==7 else 12; tip=seat-length
        screws.append(dict(xy_mm=[x,y],measured_lid_probe_hits_z_mm=lh,measured_boss_probe_hits_z_mm=bh,
            seat_z_mm=seat,suggested_thread='M2.5; tap 2.1mm printed pilot after a test coupon',
            suggested_under_head_length_mm=length,maximum_head_diameter_mm=4.5,screw_tip_z_mm=tip,
            nominal_thread_engagement_mm=max(0,min(bh[-1],seat)-max(1.5,tip))))
    theta=np.linspace(0,2*np.pi,361)[:-1]
    head=np.column_stack([92+2.25*np.cos(theta),92+2.25*np.sin(theta),np.full_like(theta,screws[-1]['seat_z_mm'])])
    mic=labelled['MIC']['points']; head_mic=min(point_segment_min(head,mic),point_segment_min(mic,head))
    head_mic_xy=min(point_segment_min(head[:,:2],mic[:,:2]),point_segment_min(mic[:,:2],head[:,:2]))
    capacitors=[]
    for ref,xy,height in [('C3',(58.5,9),12.5),('C_VM',(25.5,25.5),12.5),('C1',(31.5,9),11.0)]:
        envelope=Manifold.cylinder(height,3.15,3.15,circular_segments=128).translate([xy[0],xy[1],8.1])
        roof=vertical_hits(lid,*xy)[0]
        capacitors.append(dict(reference=ref,case_xy_mm=list(xy),pcb_top_z_mm=8.1,nominal_diameter_mm=6.3,
            checked_body_height_mm=height,body_top_z_mm=8.1+height,measured_roof_z_mm=roof,
            centre_vertical_roof_clearance_mm=roof-8.1-height,base_overlap_mm3=overlap(base,envelope),lid_overlap_mm3=overlap(lid,envelope),
            scope='Nominal D6.3 vertical cylinder only; Rubycon max L12.5, C1 nominal L11; leads/standoff/diameter tolerance NOT verified'))
    angle=math.degrees(math.acos(n[2])); total=sum(r['volume_cm3'] for r in [b,l,g])
    report=dict(method='Independent exported-STL topology, planar boundary extraction, segment distance and Boolean blank-board sweep; never imports CAD.',
        parts=[b,l,g],total_volume_cm3=total,volume_limit_cm3=70,
        panel=dict(normal=n.tolist(),plane_constant_mm=d,angle_degrees=angle,measured_normal_thickness_mm=panel_thickness,
                   openings={k:{a:v for a,v in o.items() if a not in ['points','uv']} for k,o in labelled.items()}),
        top_deck=dict(probe_xy_mm=[20.123,30.321],measured_intersections_z_mm=top_hits,measured_thickness_mm=top_hits[-1]-top_hits[-2],bottom_intersections_z_mm=bottom_hits,
                      measured_flat_region_cavity_height_mm=top_hits[0]-bottom_hits[-1]),
        oled_ec11=dict(measured_surface_edge_gap_mm=gap,meets_13mm=gap>=13,meets_16mm=gap>=16,
            analytic_crosscheck_mm=24/math.cos(math.radians(angle))-8.25-4.5,fixed_centres_can_reach_16mm=False,
            minimum_ec11_y_for_16_if_oled_y64_mm=64+(16+8.25+4.5)*math.cos(math.radians(angle))),buttons=buttons,
        pcb_access=dict(measured_split_z_mm=float(base.bounds[1,2]),measured_inner_x_walls_mm=inner_x,
            measured_clear_width_mm=inner_x[1]-inner_x[0],assumed_board_bounds_mm=[[2,2,6.5],[97,97,8.1]],
            measured_boss_probe_hits_z_mm=boss_hits,bare_board_base_intersection_mm3=bv,bare_board_closed_lid_intersection_mm3=lv,
            vertical_insertion_sweep_intersection_mm3=iv,base_lid_intersection_mm3=seam,
            result='Bare 95x95x1.6 PCB only; populated PCB and cable/module envelopes NOT verified'),
        lid_screws=screws,front_right_head_seat_circle_to_mic_boundary_distance_mm=head_mic,
        front_right_head_projected_xy_clearance_to_mic_mm=head_mic_xy,capacitor_envelopes=capacitors,
        section_evidence=section_image(base,lid),assembly_release=False,
        limitations=['Only bare-board access is tested; real populated board and module bodies were not supplied.',
            'Button protrusion is at hole centre ONLY, conditional on module PCB bottom Z8.1 and vertical 15mm stack. Whole-cap edge protrusion, module support/fixings and cap size/travel are unknown.',
            'Buttons have local raised 25-degree faces; 7mm vertical bores have elliptical outlines. Main slope is not raised.',
            'M2.5 lid screws share PCB mount locations. Verify actual PCB holes, keepout and thickness; front-right head <=4.5mm without washer near MIC.',
            'Tapped resin pilots and long screws need coupon tests; no gasket, alignment tongue or strength/thermal/vibration validation.',
            'OLED/EC11/PAJ/MIC bodies, servo spline/retention, motor holding, wiring, supports and shrinkage remain unverified.',
            'Gimbal saddle is 3mm, non-load-rated wing floors 2mm; slot residual floor 0.5mm is not strength-rated.'])
    report['geometry_acceptance_pass']=bool(all(r['pass'] for r in [b,l,g]) and total<=70 and gap>=13 and abs(panel_thickness-2)<.01
        and top_hits==[30.0,32.0] and bottom_hits==[0.0,2.0] and max(abs(v) for v in [bv,lv,iv,seam])<1e-5
        and abs(inner_x[1]-inner_x[0]-95.8)<.01 and abs(angle-25)<.001 and head_mic_xy>0
        and np.allclose(labelled['OLED']['size_surface_mm'],[28,16.5],atol=.01)
        and np.allclose(labelled['EC11']['size_surface_mm'],[9,9],atol=.01)
        and all(abs(c['base_overlap_mm3'])<1e-5 and abs(c['lid_overlap_mm3'])<1e-5 for c in capacitors)
        and all(1.2<=v['conditional_vertical_protrusion_mm']<=1.5 and abs(v['measured_surface_bore_size_mm'][0]-7)<.01 for v in buttons.values()))
    out=ROOT/'mechanical/P2_mechanical_verification.json'
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if not report['geometry_acceptance_pass']: raise SystemExit(1)


if __name__=='__main__': main()
