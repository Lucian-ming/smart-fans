"""Run independent RevB validators and preserve their unabridged output."""
from pathlib import Path
import subprocess, sys, json, hashlib, argparse
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/fabrication/validation'
CHECKS=[
 ('单5V供电与核心板电气语义',['tools/test_revb_electrical_semantics.py']),
 ('MCU非镜像40针映射',['tools/test_core_header_mapping.py','--check-production']),
 ('ASR16针及三跳帽隔离',['tools/test_asr_interface_ast.py']),
 ('实测TB6612直插针序',['tools/test_tb6612_interface_ast.py']),
 ('实测2+3编码器接口',['tools/test_ec23_interface_ast.py']),
 ('连接器与准确物料回归',['tools/test_revb_exact_parts_ast.py']),
 ('OLED安装方向与针序',['tools/test_oled_installation_ast.py']),
 ('过孔盖油正反例',['tools/test_revb_via_tenting.py']),
 ('宽功率线覆铜切削精度',['tools/test_revb_track_cutout.py']),
 ('PCB铜间距与网络连通性',['tools/verify_revb_copper.py']),
 ('供电主干宽度及受限逃逸连通',['tools/verify_revb_power.py','--pcb','hardware/kicad/fan_ctrl_revB.kicad_pcb','--router-report','hardware/fabrication/validation/router_report.json','--report','hardware/fabrication/validation/power_audit.json']),
 ('原理图引脚与顶层丝印',['tools/validate_revB_schematic.py','--report','artifacts/revB_schematic_validation.json','--gto','hardware/fabrication/gerber_revB/fan_ctrl_revB.GTO']),
 ('Gerber及Excellon几何一致性',['tools/validate_revB_gerber_geometry.py']),
 ('板边、钻孔、阻焊及丝印制造检查',['tools/verify_revb_manufacturing.py']),
 ('三件STL及机械装配约束',['tools/verify_smartfan_mechanical.py']),
]
def main():
 sys.stdout.reconfigure(encoding='utf8')
 parser=argparse.ArgumentParser()
 parser.add_argument('--pcb-only',action='store_true',help='只验证当前PCB，不将旧外壳验收混入新电气版本')
 options=parser.parse_args()
 checks=[c for c in CHECKS if not (options.pcb_only and 'STL' in c[0])]
 OUT.mkdir(parents=True,exist_ok=True)
 results=[]
 for i,(name,args) in enumerate(checks):
  r=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
  log=OUT/f'check_{i+1}.log'
  log.write_text(r.stdout+'\nSTDERR:\n'+r.stderr,encoding='utf8')
  print(f"{'PASS' if r.returncode==0 else 'FAIL'} {name} (exit {r.returncode})",flush=True)
  print(r.stdout,flush=True)
  if r.returncode:print(r.stderr,flush=True)
  results.append(dict(name=name,exit_code=r.returncode,log=str(log.relative_to(ROOT))))
 sources={}
 for pattern in ['tools/*revB*.py','tools/*revb*.py','tools/*smartfan*.py','tools/obstacle_router.py','tools/test_router*.py','tools/test_*interface_ast.py','tools/test_oled_installation_ast.py','tools/test_core_header_mapping.py','hardware/fabrication/BOM_SmartFan_RevB.xlsx','hardware/kicad/fan_ctrl_revB.kicad_*','hardware/fabrication/gerber_revB/*','mechanical/stl/print/*.stl']:
  for p in ROOT.glob(pattern):
   if options.pcb_only and p.suffix.lower()=='.stl':continue
   sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 summary=dict(created_at=datetime.now().astimezone().isoformat(),scope='pcb_prototype_only' if options.pcb_only else 'pcb_and_mechanical',automatic_checks_pass=all(r['exit_code']==0 for r in results),checks=results,sha256=sources,limitations=['未执行KiCad原生DRC/ERC/网表导出。','未确认供应商实时库存；真实料号不等于现货承诺。','模块直插以说明书中的实测及安装条件为边界；未完成整机实体装配，旧外壳未随本次PCB改版验证。' if options.pcb_only else '机械按键露出量以指定安装Z和竖直15mm高度为条件；未替代完整实体装配。','样机仍需验证供电压降、纹波、温升和电机启动/堵转工况；几何合格不等于电气或整机生产签核。'])
 (OUT/'validation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 return 0 if summary['automatic_checks_pass'] else 1
if __name__=='__main__':sys.exit(main())
