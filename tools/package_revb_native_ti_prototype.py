"""Package only hash-bound native manufacturing artifacts after final audit; never reuse legacy Gerbers."""
from pathlib import Path
import hashlib,json,zipfile,shutil,datetime
from openpyxl import load_workbook
R=Path(__file__).resolve().parents[1]
C=R/'artifacts/native_pcb_review/candidate_tlv1117'
B=R/'artifacts/tlv1117_rebuild_input_v2/hardware/fabrication/BOM_SmartFan_RevB.xlsx'
def need(ok,message):
    if not ok: raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((C/name).read_text(encoding='utf8'))
s=read('run_summary.json');a=read('final_fabrication_audit.json')
expected={'baseline_netlist','convert_sch','netlist','connections','convert_pcb','erc','drc_parity','invariance','native_gerbers','native_drill'}
need(s.get('all_steps_pass') is True and len(s['steps'])==10 and {x['step'] for x in s['steps']}==expected and all(type(x['exit_code']) is int and x['exit_code']==0 for x in s['steps']),'Native pipeline incomplete')
need(a.get('passed') is True and a.get('errors')==[],'Final manufacturing audit failed or absent')
for rel,h in s['output_sha256'].items():need(sha(C/rel)==h,'Native artifact changed: '+rel)
for path,h in a['file_sha256'].items():need(sha(Path(path))==h,'Audited artifact changed: '+path)
expected_audited={str((C/'fan_ctrl_revB.kicad_pcb').resolve()):sha(C/'fan_ctrl_revB.kicad_pcb')}
for p in (C/'native_manufacturing').iterdir():
    if p.suffix in {'.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1','.drl'}:expected_audited[str(p.resolve())]=sha(p)
need({str(Path(p).resolve()):h for p,h in a['file_sha256'].items()}==expected_audited and len(expected_audited)==12,'Audit is not bound to exact PCB and eleven manufacturing layers')
d=read('drc_parity.json');e=read('erc.json')
need(all(d.get(k)==[] for k in ['violations','unconnected_items','schematic_parity']),'Native DRC is not zero')
need(e.get('sheets') and all(x['violations']==[] for x in e['sheets']),'Native ERC is not zero')
w=load_workbook(B,read_only=True,data_only=True)
rows=[row for row in w.active.iter_rows(values_only=True) if 'U3' in str(row[1]).replace(' ','').split(',')]
need(len(rows)==1 and rows[0][3]=='TLV1117LV33DCYR' and rows[0][5]=='C15578' and rows[0][6]=='TLV1117LV33DCYR' and rows[0][7]=='Texas Instruments','BOM U3 mismatch');w.close()
report='''# RevB 单5V / TI稳压器版审核结果

范围：少量裸板工程验证，不是整机或量产签核。旧版包继续禁用。

## 本次真实执行
- KiCad 10.0.7原生转换、网表对照、ERC、DRC、原理图一致性、几何保真、原生Gerber及钻孔导出：10/10步骤通过。
- ERC报告违规0；DRC报告违规0、未连接0、原理图一致性差异0。默认忽略项保留在原始JSON，不声称开启了所有默认关闭规则。
- 新版48元件、173物理焊盘、2730线段、84过孔；原生转换前后实际连接集合及元件/走线几何一致，铺铜由KiCad重新生成。
- U3：TI TLV1117LV33DCYR / C15578；原厂DCY焊盘包络已核，BOM已核。
- 独立最终Gerber/钻孔审计通过；明确Y坐标转换，无buffer(0)修补畸形铜。导出精度1000nm，验收阈值未放宽。

## 条件仿真与未测项
LTspice已真实执行18组I2C RC和18组总供电回路扫描。条件中I2C标准模式4组超上升时间、快速模式12组超标；供电6组低于4.5V、最低约4.15V。这些是风险边界，不是实际负载失败或整机通过。
无准确电机/舵机模型、无实测启动/堵转电流、纹波或温升。稳压器更换依据原厂稳定性要求，不是假装已完成该器件闭环SPICE/实物验收。用户无测量仪器，建议借设备或委托上电检查。

完整接口、USB反供、OLED实体适配、固件及机械限制见同目录Prototype_Notes.md；这些风险不会因DRC归零而消失。

## 独立制造检查数据
```json
'''+json.dumps(a['metrics'],ensure_ascii=False,indent=2)+'\n```\n\n原始记录在evidence目录。Gerber ZIP来自本次原生候选，绝未使用手工铺铜旧ZIP。\n'
D=Path('D:/下载')/('RevB_5V_TI_NATIVE_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
need(not D.exists(),'Destination already exists');D.mkdir()
for name in ['fan_ctrl_revB.kicad_pcb','fan_ctrl_revB.kicad_sch','fan_ctrl_revB.kicad_pro','fp-lib-table','sym-lib-table','RevB_Symbols.kicad_sym','Prototype_Notes.md']:
    shutil.copy2(C/name,D/name)
shutil.copytree(C/'RevB_Snapshot.pretty',D/'RevB_Snapshot.pretty')
shutil.copy2(B,D/'BOM_SmartFan_RevB_5V_TI.xlsx')
(D/'Audit_Report.md').write_text(report,encoding='utf8')
G=C/'native_manufacturing';members=sorted(p for p in G.iterdir() if p.is_file())
need(len([p for p in members if p.suffix=='.drl'])==2,'Missing split drills')
with zipfile.ZipFile(D/'Gerber_RevB_5V_TI_NATIVE.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in members:z.write(p,p.name)
with zipfile.ZipFile(D/'Gerber_RevB_5V_TI_NATIVE.zip') as z:
    need(set(z.namelist())=={p.name for p in members},'ZIP member mismatch')
    for p in members:need(z.read(p.name)==p.read_bytes(),'ZIP bytes mismatch')
E=D/'evidence';E.mkdir()
for name in ['run_summary.json','erc.json','drc_parity.json','connectivity_comparison.json','geometry_invariance.json','precision_change.json','final_fabrication_audit.json']:
    shutil.copy2(C/name,E/name)
for name in ['conditional_simulation_results.json','tlv1117lv_footprint_evidence.md','user_reference_code_review.md']:
    shutil.copy2(R/'artifacts/simulation_review'/name,E/name)
# Verify every copied primary native artifact against its verified source bytes.
for name in ['fan_ctrl_revB.kicad_pcb','fan_ctrl_revB.kicad_sch','fan_ctrl_revB.kicad_pro','fp-lib-table','sym-lib-table','RevB_Symbols.kicad_sym','Prototype_Notes.md']:
    need(sha(D/name)==sha(C/name),'Copy verification failed '+name)
need(sha(D/'BOM_SmartFan_RevB_5V_TI.xlsx')==sha(B),'BOM copy mismatch')
manifest={'scope':'bare_board_engineering_prototype_only','system_release_approved':False,'native_manufacturing_checks_pass':True,'source_summary_sha256':sha(C/'run_summary.json'),'final_audit_sha256':sha(C/'final_fabrication_audit.json'),'files':{str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file()}}
(D/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'destination':str(D),'native_checks_pass':True,'system_release_approved':False,'files':len(manifest['files'])},ensure_ascii=False,indent=2))
