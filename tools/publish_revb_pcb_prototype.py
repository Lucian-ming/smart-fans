"""Publish six explicitly reviewed PCB prototype deliverables, never full assembly approval."""
from pathlib import Path
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'hardware/fabrication/validation'
PAIRS = [
 ('hardware/kicad/fan_ctrl_revB.kicad_pcb', 'fan_ctrl_revB_5V.kicad_pcb'),
 ('hardware/kicad/fan_ctrl_revB.kicad_sch', 'fan_ctrl_revB_5V.kicad_sch'),
 ('hardware/fabrication/Gerber_fan_ctrl_revB_2026-11-04.zip', 'Gerber_fan_ctrl_revB_5V.zip'),
 ('hardware/fabrication/BOM_SmartFan_RevB.xlsx', 'BOM_SmartFan_RevB_5V.xlsx'),
 ('hardware/fabrication/RevB_5V_Validation_Report.md', 'RevB_5V_Validation_Report.md'),
 ('hardware/fabrication/RevB_5V_Prototype_Notes.md', 'RevB_5V_Prototype_Notes.md'),
]
REQUIRED_CHECKS = {
 '单5V供电与核心板电气语义', 'MCU非镜像40针映射', 'ASR16针及三跳帽隔离',
 '实测TB6612直插针序', '实测2+3编码器接口', '连接器与准确物料回归',
 'OLED安装方向与针序', '过孔盖油正反例', '宽功率线覆铜切削精度',
 'PCB铜间距与网络连通性', '供电主干宽度及受限逃逸连通',
 '原理图引脚与顶层丝印', 'Gerber及Excellon几何一致性', '板边、钻孔、阻焊及丝印制造检查',
}
GERBER_NAMES = {f'fan_ctrl_revB.{e}' for e in ('GTL','GBL','GTS','GBS','GTO','GBO','GKO','DRL')}
GERBER_DIR = 'hardware/fabrication/gerber_revB/'
REQUIRED_HASHES = {PAIRS[i][0] for i in (0,1,3)} | {GERBER_DIR+n for n in GERBER_NAMES}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(p):
    return sha(p.read_bytes())

def normalized_hashes(mapping):
    require(isinstance(mapping, dict), 'Hash map must be an object')
    result = {}
    for name, value in mapping.items():
        require(isinstance(name, str), 'Hash path must be text')
        key = name.replace('\\', '/')
        require(not key.startswith('/') and ':' not in key and all(x not in ('', '.', '..') for x in key.split('/')), 'Unsafe source path')
        require(key not in result, 'Duplicate normalized hash path')
        require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'Invalid SHA256')
        result[key] = value
    return result

def validate_release(root, summary_bytes, review):
    """Read-only preflight; return immutable snapshots of all six reviewed sources."""
    summary = json.loads(summary_bytes)
    require(summary.get('automatic_checks_pass') is True, 'Failed automatic checks prohibit publication')
    checks = summary.get('checks')
    require(isinstance(checks, list) and len(checks) == 14, 'Exactly 14 checks required')
    require(all(isinstance(c, dict) for c in checks), 'Invalid check record')
    names = [c.get('name') for c in checks]
    require(all(isinstance(n, str) for n in names) and len(set(names)) == 14 and set(names) == REQUIRED_CHECKS, 'Missing, duplicate or unexpected checks')
    require(all(type(c.get('exit_code')) is int and c['exit_code'] == 0 for c in checks), 'All 14 checks must exit zero')
    require(review.get('status') == 'reviewed_prototype_only', 'Explicit prototype review required')
    require(review.get('scope') == 'pcb_prototype_only', 'Full assembly approval is not supported')
    require(review.get('validation_summary_sha256') == sha(summary_bytes), 'Review does not bind this validation summary')
    limits = review.get('unresolved_limits')
    require(isinstance(limits, list) and bool(limits) and all(isinstance(x, str) and x.strip() for x in limits), 'Prototype limitations must be disclosed')
    verified = normalized_hashes(summary.get('sha256'))
    require(REQUIRED_HASHES <= set(verified), 'Missing PCB/SCH/BOM or eight Gerber hashes')
    reviewed = normalized_hashes(review.get('source_sha256'))
    require(set(reviewed) == {p[0] for p in PAIRS}, 'Review must bind exactly all six deliverables including both final documents')
    snapshots = {}
    for name in set(verified) | set(reviewed):
        data = (root/name).read_bytes()
        if name in verified:
            require(sha(data) == verified[name], f'Changed after verification: {name}')
        if name in reviewed:
            require(sha(data) == reviewed[name], f'Changed after review: {name}')
        snapshots[name] = data
    with zipfile.ZipFile(io.BytesIO(snapshots[PAIRS[2][0]])) as z:
        require(z.testzip() is None, 'Corrupt Gerber archive')
        members = [n for n in z.namelist() if not n.endswith('/')]
        require(len(members) == 8 and set(members) == GERBER_NAMES, 'Archive must contain exactly eight unique flat manufacturing files')
        for name in members:
            require(z.read(name) == snapshots[GERBER_DIR+name], f'Archive differs from verified Gerber: {name}')
    return {source: snapshots[source] for source, _ in PAIRS}

def main():
    summary_bytes = (V/'validation_summary.json').read_bytes()
    review = json.loads((V/'pcb_prototype_release_review.json').read_text(encoding='utf8'))
    data = validate_release(ROOT, summary_bytes, review)
    dest = Path(review['destination'])
    require(dest.parent == Path('D:/下载') and dest.name.startswith('RevB_5V_'), 'Unexpected destination')
    dest.mkdir(exist_ok=False)
    files = []
    for source, name in PAIRS:
        out = dest/name
        with out.open('xb') as f:
            f.write(data[source])
        require(out.read_bytes() == data[source], f'Delivery copy mismatch: {name}')
        files.append({'source':str(ROOT/source), 'target':str(out), 'sha256':sha(data[source]), 'bytes':len(data[source])})
    manifest = {'scope':'pcb_prototype_only', 'qualification':'Not full assembly or production qualification',
        'files':files, 'file_count':6, 'all_hashes_match':True, 'review':review,
        'additional_evidence_files':['pcb_prototype_delivery_manifest.json'],
        'evidence_note':'Manifest is a seventh evidence file, not a seventh primary deliverable; no self-hash.'}
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    with (dest/'pcb_prototype_delivery_manifest.json').open('x', encoding='utf8') as f:
        f.write(text)
    (V/'pcb_prototype_delivery_manifest.json').write_text(text, encoding='utf8')
    print(json.dumps(manifest, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    main()
