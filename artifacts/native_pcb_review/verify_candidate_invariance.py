from pathlib import Path
import pcbnew,json,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--pcb',default='hardware/kicad/fan_ctrl_revB.kicad_pcb');ap.add_argument('--out',default='artifacts/native_pcb_review/candidate');args=ap.parse_args()
R=Path(args.out).resolve()
def vec(p):return [p.x,p.y]
def snapshot(path):
 b=pcbnew.LoadBoard(str(path));fps=[]
 for f in b.GetFootprints():
  pads=[]
  for p in f.Pads():pads.append([p.GetNumber(),vec(p.GetPosition()),vec(p.GetSize()),vec(p.GetDrillSize()),int(p.GetShape()),int(p.GetAttribute()),p.GetOrientationDegrees(),list(p.GetLayerSet().Seq())])
  fps.append([f.GetReference(),f.GetValue(),vec(f.GetPosition()),f.GetOrientationDegrees(),sorted(pads,key=str)])
 tracks=[]
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA):tracks.append(['via',vec(t.GetPosition()),[[l,t.GetWidth(l)] for l in t.GetLayerSet().Seq()],t.GetDrillValue(),list(t.GetLayerSet().Seq()),t.GetNetname()])
  else:tracks.append(['track',vec(t.GetStart()),vec(t.GetEnd()),t.GetWidth(),t.GetLayer(),t.GetNetname()])
 edge=[]
 for d in b.GetDrawings():
  if d.GetLayer()==pcbnew.Edge_Cuts:edge.append([int(d.GetShape()),vec(d.GetStart()),vec(d.GetEnd()),d.GetWidth()])
 return {'footprints':sorted(fps,key=str),'tracks_vias':sorted(tracks,key=str),'edge_cuts':sorted(edge,key=str)}
src=Path(args.pcb).resolve();before=snapshot(src);after=snapshot(R/'fan_ctrl_revB.kicad_pcb')
report={'unchanged_footprint_placement_and_pad_geometry':before['footprints']==after['footprints'],'unchanged_tracks_and_vias_including_net_names':before['tracks_vias']==after['tracks_vias'],'unchanged_edge_cuts':before['edge_cuts']==after['edge_cuts'],'footprint_count':len(after['footprints']),'tracks_vias_count':len(after['tracks_vias']),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scope':'Filled zones intentionally regenerated natively with full pad connection; pad NC names and fields intentionally synchronized.'}
(R/'geometry_invariance.json').write_text(json.dumps(report,indent=2),encoding='utf8')
assert all(report[k] for k in report if k.startswith('unchanged_')),report
print(report)
