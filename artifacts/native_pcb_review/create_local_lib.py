from pathlib import Path
import pcbnew,json
root=Path('artifacts/native_pcb_review').resolve()
board=pcbnew.LoadBoard(str(root/'solid_gnd.kicad_pcb'))
lib=root/'RevB_Snapshot.pretty';lib.mkdir(exist_ok=True)
manifest=[]
for fp in board.GetFootprints():
 ref=fp.GetReference(); old=fp.GetFPIDAsString();name='Board_'+ref
 fp.SetFPIDAsString('RevB_Snapshot:'+name)
 pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),fp)
 if not (lib/(name+'.kicad_mod')).is_file():raise RuntimeError('Cannot save '+ref)
 manifest.append({'reference':ref,'original_id':old,'local_id':fp.GetFPIDAsString(),'provenance':'Exact board snapshot, NOT independent footprint dimension certification'})
(root/'fp-lib-table').write_text('(fp_lib_table\n (version 7)\n (lib (name "RevB_Snapshot")(type "KiCad")(uri "${KIPRJMOD}/RevB_Snapshot.pretty")(options "")(descr "Exact PCB snapshot library; dimensional audit separate"))\n)\n',encoding='utf8')
pcbnew.SaveBoard(str(root/'solid_local.kicad_pcb'),board)
(root/'local_library_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('Saved',len(manifest),'library items')
