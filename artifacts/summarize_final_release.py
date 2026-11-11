from pathlib import Path
import json, hashlib
root=Path('D:/smart_fans')
for rel in ['hardware/fabrication/validation/validation_summary.json','hardware/fabrication/validation/copper_audit.json','hardware/fabrication/validation/manufacturing_audit.json','hardware/fabrication/validation/power_audit.json','artifacts/revB_schematic_validation.json']:
 p=root/rel;d=json.loads(p.read_text(encoding='utf8'))
 print('\nFILE',rel,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 print(json.dumps({k:v for k,v in d.items() if not isinstance(v,(list,dict))},ensure_ascii=True))
 print('KEYS',list(d))
 if 'checks' in d: print(json.dumps(d['checks'],ensure_ascii=True))
 if 'failures' in d: print('FAILURES',d['failures'])
 if 'drill' in d: print('DRILL',json.dumps({k:v for k,v in d['drill'].items() if k!='violations'}))
 if 'connectivity' in d: print('CONNECTIVITY',json.dumps({k:v for k,v in d['connectivity'].items() if not isinstance(v,(list,dict))}))
