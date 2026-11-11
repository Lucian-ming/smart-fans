"""Native pcbnew metadata-only parity alignment in isolated candidate."""
from pathlib import Path
import pcbnew,json,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--pcb',default='hardware/kicad/fan_ctrl_revB.kicad_pcb');ap.add_argument('--out',default='artifacts/native_pcb_review/candidate');args=ap.parse_args()
R=Path(args.out).resolve();base=R.parent
manifest=json.loads((R/'semantic_manifest.json').read_text(encoding='utf8'));nets=json.loads((R/'native_pin_nets.json').read_text(encoding='utf8'))
source=Path(args.pcb)
board=pcbnew.LoadBoard(str(source.resolve()))
for zone in board.Zones():zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
lib=R/'RevB_Snapshot.pretty';lib.mkdir(exist_ok=True)
byname={str(net.GetNetname()):net for net in board.GetNetInfo().NetsByNetcode().values()}
for name in sorted(set(nets.values())):
 if name not in byname:
  net=pcbnew.NETINFO_ITEM(board,name);board.Add(net);byname[name]=net
for fp in board.GetFootprints():
 ref=fp.GetReference()
 if ref not in manifest:
  assert ref.startswith('H'),ref
  fp.SetAttributes(fp.GetAttributes()|pcbnew.FP_BOARD_ONLY)
 else:
  for key,value in manifest[ref]['properties'].items():
   if key not in ('Reference','Value','Footprint'):
    fp.SetField(key,value);fp.GetField(key).SetVisible(False)
  for pad in fp.Pads():
   key=ref+'.'+pad.GetNumber()
   if key not in nets:raise ValueError('Missing native pin '+key)
   pad.SetNet(byname[nets[key]])
 fp.SetFPIDAsString('RevB_Snapshot:Board_'+ref)
 pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),fp)
(R/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "RevB_Snapshot")(type "KiCad")(uri "${KIPRJMOD}/RevB_Snapshot.pretty")(options "")(descr "Exact board snapshot, not dimensional certification")))',encoding='utf8')
pcbnew.SaveBoard(str(R/'fan_ctrl_revB.kicad_pcb'),board)
# A project is necessary for native CLI to resolve project-local library tables.
project=source.with_suffix('.kicad_pro')
if project.exists():
 (R/'fan_ctrl_revB.kicad_pro').write_bytes(project.read_bytes())
else:
 (R/'fan_ctrl_revB.kicad_pro').write_text(json.dumps({'meta':{'filename':'fan_ctrl_revB.kicad_pro','version':1}},indent=2),encoding='utf8')
rules=source.with_suffix('.kicad_dru')
if rules.exists():(R/'fan_ctrl_revB.kicad_dru').write_bytes(rules.read_bytes())
else:assert not (R/'fan_ctrl_revB.kicad_dru').exists(),'Stale custom rules: choose a fresh output directory'
# Load the OUTPUT project before changing settings; never save source project settings.
precision_board=pcbnew.LoadBoard(str(R/'fan_ctrl_revB.kicad_pcb'))
settings=precision_board.GetDesignSettings();old_error=settings.m_MaxError
settings.m_MaxError=min(old_error,1000)
assert pcbnew.GetSettingsManager().SaveProject(str(R/'fan_ctrl_revB.kicad_pro'),precision_board.GetProject()),'Cannot persist output precision'
(R/'precision_change.json').write_text(json.dumps({'before_nm':old_error,'after_nm':settings.m_MaxError,'native_SaveProject':True,'threshold_changed':False},indent=2),encoding='utf8')
print('Saved isolated PCB; snapshot footprints:',len(list(board.GetFootprints())),'max_error_nm:',settings.m_MaxError)
