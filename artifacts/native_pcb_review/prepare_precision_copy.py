from pathlib import Path
import shutil,pcbnew,json
src=Path('artifacts/native_pcb_review/candidate').resolve();out=src.with_name('candidate_precision_001')
assert not out.exists(),'Use a new isolated directory'
shutil.copytree(src,out)
p=out/'fan_ctrl_revB.kicad_pcb';b=pcbnew.LoadBoard(str(p));s=b.GetDesignSettings();before=s.m_MaxError;s.m_MaxError=1000
pcbnew.SaveBoard(str(p),b)
ok=pcbnew.GetSettingsManager().SaveProject(str(out/'fan_ctrl_revB.kicad_pro'),b.GetProject())
assert ok,'Native SaveProject failed'
(out/'precision_change.json').write_text(json.dumps({'before_nm':before,'after_nm':s.m_MaxError,'native_SaveProject':ok,'threshold_changed':False},indent=2),encoding='utf8')
print(before,s.m_MaxError,ok)
