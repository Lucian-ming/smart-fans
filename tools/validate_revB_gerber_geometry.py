"""Independent PCB/Gerber/Excellon geometric consistency audit (read-only)."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from gerbonara import GerberFile, ExcellonFile
from gerbonara.graphic_objects import Flash, Region, Arc, Line
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from validate_revB_schematic import parse, one, children, xy
from strict_copper_geometry import strict_region, require_dark, checked_main

ROOT = Path(__file__).resolve().parents[1]

def audit_tented_masks(pcb, gerbers):
    """Compare real mask flashes to serialized PCB pads and audit actual via-hole cover.

    The 0.10 mm hole-edge cover is a design gate, NOT a board-fabricator-certified
    tenting annulus or a guarantee that liquid solder mask will seal a drilled hole.
    No same-net exceptions; copper and Excellon checks remain independent.
    """
    from gerbonara.apertures import CircleAperture, RectangleAperture
    errors, summary = [], {}
    setup = one(pcb, 'setup')
    plot = children(setup, 'pcbplotparams')
    setting = children(plot[0], 'viasonmask') if plot else []
    if len(setting) != 1 or str(setting[0][1]) != 'false':
        errors.append({'kind': 'via_tenting_not_explicit'})
    margin = float(one(setup, 'pad_to_mask_clearance')[1])
    def key(shape, x, y, w, h):
        return (shape, round(x, 5), round(y, 5), round(w, 5), round(h, 5))
    for layer, ext in [('F.Mask', 'GTS'), ('B.Mask', 'GBS')]:
        expected, actual, openings = Counter(), Counter(), []
        for fp in children(pcb, 'footprint'):
            at = one(fp, 'at'); fx, fy = xy(at)
            for p in children(fp, 'pad'):
                layers = [str(v) for v in one(p, 'layers')[1:]]
                if layer not in layers and '*.Mask' not in layers:
                    continue
                pa = one(p, 'at')
                if (len(at) > 3 and float(at[3]) % 360) or (len(pa) > 3 and float(pa[3]) % 360) or children(p, 'solder_mask_margin') or children(fp, 'solder_mask_margin'):
                    errors.append({'kind': 'unsupported_mask_transform_or_override', 'pin': p[1]})
                    continue
                px, py = xy(pa); w, h = xy(one(p, 'size'))
                shape = str(p[3])
                if shape not in ('circle', 'rect'):
                    errors.append({'kind': 'unsupported_mask_pad_shape', 'shape': shape})
                    continue
                expected[key(shape, fx+px, fy+py, w+2*margin, h+2*margin)] += 1
        for o in GerberFile.open(Path(gerbers)/f'fan_ctrl_revB.{ext}').objects:
            if not isinstance(o, Flash) or not o.polarity_dark:
                errors.append({'kind': 'unsupported_mask_object', 'layer': layer})
                continue
            a = o.aperture
            if isinstance(a, CircleAperture):
                actual[key('circle', o.x, o.y, a.diameter, a.diameter)] += 1
                openings.append(Point(o.x, o.y).buffer(a.diameter/2/math.cos(math.pi/1024), quad_segs=256))
            elif isinstance(a, RectangleAperture):
                actual[key('rect', o.x, o.y, a.w, a.h)] += 1
                openings.append(box(o.x-a.w/2, o.y-a.h/2, o.x+a.w/2, o.y+a.h/2))
            else:
                errors.append({'kind': 'unsupported_mask_aperture', 'layer': layer})
        if expected != actual:
            errors.append({'kind': 'mask_geometry_mismatch', 'layer': layer, 'missing': list((expected-actual).elements()), 'extra': list((actual-expected).elements())})
        mask = unary_union(openings)
        checks = []
        for v in children(pcb, 'via'):
            x, y = xy(one(v, 'at')); radius = float(one(v, 'drill')[1])/2
            # Point-to-opening minus analytic drill radius avoids polygonized-hole optimism.
            gap = Point(x, y).distance(mask)-radius if not mask.is_empty else None
            checks.append({'xy': [x,y], 'hole_edge_to_mask_mm': gap})
            if gap is not None and gap < .10-1e-6:
                errors.append({'kind': 'via_tent_cover_clearance', 'layer': layer, **checks[-1]})
        summary[layer] = {'opening_count': sum(actual.values()), 'via_count': len(checks), 'minimum_hole_cover_mm': min((r['hole_edge_to_mask_mm'] for r in checks if r['hole_edge_to_mask_mm'] is not None), default=None), 'via_checks': checks}
    summary['cover_requirement_mm'] = .10
    summary['fabricator_certified'] = False
    summary['note'] = 'Design gate only; board-fabricator tenting capability and registration allowance not certified.'
    return errors, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pcb',type=Path,default=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_pcb')
    ap.add_argument('--gerbers',type=Path,default=ROOT/'hardware/fabrication/gerber_revB')
    ap.add_argument('--report',type=Path,default=ROOT/'artifacts/revB_gerber_geometry.json')
    args = ap.parse_args()
    pcb = parse(args.pcb.read_text(encoding='utf8'))
    pads = []
    for fp in children(pcb,'footprint'):
        fx,fy = xy(one(fp,'at'))
        ref = next(n[2] for n in children(fp,'property') if n[1]=='Reference')
        for p in children(fp,'pad'):
            px,py = xy(one(p,'at'))
            w,h = xy(one(p,'size'))
            nid = int(one(p,'net')[1])
            pos = fx+px,fy+py
            geom = Point(pos).buffer(w/2, quad_segs=128) if p[3]=='circle' else box(pos[0]-w/2,pos[1]-h/2,pos[0]+w/2,pos[1]+h/2)
            pads.append(dict(ref=ref,pin=p[1],pos=pos,w=w,h=h,nid=nid,shape=p[3],smd=p[2]=='smd',geom=geom,drill=float(one(p,'drill')[1]) if children(p,'drill') else None))
    errors, distances = [], []
    summaries = {}
    mask_errors, mask_summary = audit_tented_masks(pcb, args.gerbers)
    errors.extend(mask_errors)
    summaries['tented_masks'] = mask_summary
    for layer,ext in [('F.Cu','GTL'),('B.Cu','GBL')]:
        g = GerberFile.open(args.gerbers/f'fan_ctrl_revB.{ext}')
        for i,o in enumerate(g.objects):
            require_dark(o, f'{ext} object[{i}]')
        regions = [strict_region(o, f'{ext} Region[{i}]') for i,o in enumerate(g.objects) if isinstance(o,Region)]
        ground = unary_union(regions)
        assert not ground.is_empty, ('No copper pour', ext)
        flashes = [o for o in g.objects if isinstance(o,Flash)]
        for p in pads:
            if p['smd'] and layer=='B.Cu': continue
            at = [o for o in flashes if math.dist((o.x,o.y),p['pos']) < 1e-5]
            matches = []
            for flash in at:
                aper=flash.aperture
                if p['shape']=='circle':
                    match = hasattr(aper,'diameter') and abs(aper.diameter-p['w'])<1e-5
                else:
                    match = hasattr(aper,'w') and abs(aper.w-p['w'])<1e-5 and abs(aper.h-p['h'])<1e-5
                if match: matches.append(flash)
            if len(matches)!=1:
                errors.append({'kind':'pad_aperture_match_count','layer':layer,'ref':p['ref'],'pin':p['pin'],'matching':len(matches),'all_flashes':len(at)})
            if p['nid']!=1:
                distance = ground.distance(p['geom'])
                area = ground.intersection(p['geom']).area
                distances.append({'layer':layer,'ref':p['ref'],'pin':p['pin'],'clearance_mm':distance,'overlap_mm2':area})
                if distance < 0.249 or area>1e-8:
                    errors.append({'kind':'ground_clearance','layer':layer,'ref':p['ref'],'pin':p['pin'],'clearance_mm':distance,'overlap_mm2':area})
        def keyline(x1,y1,x2,y2,width):
            return (*sorted(((round(x1,4),round(y1,4)),(round(x2,4),round(y2,4)))),round(width,4))
        want_tracks=Counter()
        for t in children(pcb,'segment'):
            if one(t,'layer')[1]==layer:
                want_tracks[keyline(*xy(one(t,'start')),*xy(one(t,'end')),float(one(t,'width')[1]))]+=1
        got_tracks=Counter(keyline(o.x1,o.y1,o.x2,o.y2,o.aperture.diameter) for o in g.objects if isinstance(o,Line))
        if want_tracks != got_tracks:
            errors.append({'kind':'track_geometry_mismatch','layer':layer,'missing':list((want_tracks-got_tracks).elements()),'extra':list((got_tracks-want_tracks).elements())})
        for v in children(pcb,'via'):
            vx,vy=xy(one(v,'at')); diameter=float(one(v,'size')[1])
            if not any(math.dist((o.x,o.y),(vx,vy))<1e-5 and hasattr(o.aperture,'diameter') and abs(o.aperture.diameter-diameter)<1e-5 for o in flashes):
                errors.append({'kind':'via_aperture_mismatch','layer':layer,'xy':[vx,vy],'diameter':diameter})
        summaries[layer]={'region_count':len(regions),'flash_count':len(flashes),'ground_area_mm2':ground.area,'track_count':sum(got_tracks.values())}
    try:
        drill = ExcellonFile.open(args.gerbers/'fan_ctrl_revB.DRL')
    except (SyntaxError, ValueError) as exc:
        drill = None
        errors.append({'kind':'drill_parse_failure','message':str(exc)})
    expected = Counter((round(p['pos'][0],3),round(p['pos'][1],3),round(p['drill'],3)) for p in pads if p['drill'] is not None)
    for via in children(pcb,'via'):
        x,y=xy(one(via,'at')); d=float(one(via,'drill')[1])
        expected[(round(x,3),round(y,3),round(d,3))]+=1
    actual = Counter((round(o.x,3),round(o.y,3),round(o.tool.diameter,3)) for o in drill.objects) if drill else Counter()
    if drill and expected != actual:
        errors.append({'kind':'drill_mismatch','missing':list((expected-actual).elements()),'extra':list((actual-expected).elements())})
    outline=GerberFile.open(args.gerbers/'fan_ctrl_revB.GKO')
    arcs=[o for o in outline.objects if isinstance(o,Arc)]
    assert len(arcs)==4
    for o in arcs:
        start=math.atan2(-o.cy,-o.cx)
        end=math.atan2(o.y2-o.y1-o.cy,o.x2-o.x1-o.cx)
        sweep=(start-end if o.clockwise else end-start)%(2*math.pi)
        if abs(sweep-math.pi/2)>1e-6: errors.append({'kind':'outline_arc_sweep','radians':sweep})
    bounds=outline.bounding_box()
    if any(abs(a-b)>0.001 for a,b in zip([*bounds[0],*bounds[1]],[99.925,99.925,195.075,195.075])):
        errors.append({'kind':'outline_bounds','actual':bounds})
    result={'pcb':str(args.pcb),'gerbers':str(args.gerbers),'pad_count':len(pads),'non_ground_pad_count':sum(p['nid']!=1 for p in pads),'clearance_cases':len(distances),'minimum_ground_clearance_mm':min(r['clearance_mm'] for r in distances),'drill_hits':sum(actual.values()),'outline_bounds':bounds,'layers':summaries,'errors':errors,'pad_clearances':distances}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='pad_clearances'},ensure_ascii=False,indent=2))
    assert not errors, f'{len(errors)} geometry errors, see {args.report}'

if __name__=='__main__': raise SystemExit(checked_main(main, ROOT/'artifacts/revB_gerber_geometry.json'))
