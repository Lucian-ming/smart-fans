"""Publish six reviewed deliverables; read/back up existing bytes and verify hashes."""
from pathlib import Path
from datetime import datetime
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
DEST=Path('D:/下载')
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 summary=json.loads((ROOT/'hardware/fabrication/validation/validation_summary.json').read_text(encoding='utf8'))
 assert summary['automatic_checks_pass'], 'Do not publish failed automatic checks'
 assert summary.get('pcb_release_approved') is True, 'Publication blocked: automatic geometry checks do not approve module footprints or electrical release; explicit reviewed pcb_release_approved is required'
 # Never publish a different PCB or STL than the validated snapshot.
 for name,expected in summary['sha256'].items():
  assert sha((ROOT/name).read_bytes())==expected, f'Changed since validation: {name}'
 items=[
 ('hardware/kicad/fan_ctrl_revB.kicad_pcb','fan_ctrl_revB.kicad_pcb'),
 ('hardware/kicad/fan_ctrl_revB.kicad_sch','fan_ctrl_revB.kicad_sch'),
 ('hardware/fabrication/Gerber_fan_ctrl_revB_2026-11-04.zip','Gerber_fan_ctrl_revB_2026-11-04.zip'),
 ('hardware/fabrication/BOM_SmartFan_RevB.xlsx','BOM_SmartFan_RevB.xlsx'),
 ('mechanical/stl/print/SmartFan_P2_Print_Kit.zip','SmartFan_Sanweihou_3D_Print_Kit_2026-11-04.zip'),
 ('hardware/fabrication/RevB_Validation_Report.md','RevB_Validation_Report.md')]
 with zipfile.ZipFile(ROOT/items[4][0]) as z:
  assert len(z.namelist())==3 and all(n.endswith('.stl') for n in z.namelist())
  for n in z.namelist():assert z.read(n)==(ROOT/'mechanical/stl/print'/Path(n).name).read_bytes()
 with zipfile.ZipFile(ROOT/items[2][0]) as z:
  assert z.testzip() is None
  for n in z.namelist():
   if not n.endswith('/'):assert z.read(n)==(ROOT/'hardware/fabrication/gerber_revB'/Path(n).name).read_bytes()
 DEST.mkdir(parents=True,exist_ok=True)
 backup=DEST/('RevB_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
 records=[]
 for rel,name in items:
  source=ROOT/rel;target=DEST/name;data=source.read_bytes();old=None;saved=None
  if target.exists():
   prior=target.read_bytes();old=sha(prior)
   backup.mkdir(exist_ok=True);saved=backup/name;saved.write_bytes(prior)
   assert saved.read_bytes()==prior
  target.write_bytes(data)
  assert target.read_bytes()==data
  records.append(dict(source=str(source),target=str(target),bytes=len(data),sha256=sha(data),previous_sha256=old,backup=str(saved) if saved else None))
 report=dict(created_at=datetime.now().astimezone().isoformat(),file_count=len(records),all_hashes_match=True,files=records,obsolete_note='Old standalone two-piece STL files were not deleted. Use the new three-STL ZIP only.')
 (ROOT/'hardware/fabrication/validation/delivery_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(report,ensure_ascii=True,indent=2))
if __name__=='__main__':main()
