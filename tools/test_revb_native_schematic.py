"""Native KiCad parser/netlist regression; ERC findings are retained, NOT waived.
Runs only isolated schematic generation under artifacts; never builds PCB or publishes.
"""
import argparse
import ast
from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
from validate_revB_schematic import load_design, parse, children, one, validate

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe')

def normalized(tree):
    tree=copy.deepcopy(tree)
    for parent in children(one(tree,'lib_symbols'),'symbol'):
        for unit in children(parent,'symbol'):
            unit[1]=parent[1].split(':')[-1]+'_'+'_'.join(unit[1].rsplit('_',2)[1:])
    return tree

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cli',type=Path,default=CLI)
    ap.add_argument('--out',type=Path,default=ROOT/'artifacts/native_sch_review')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    baseline=ROOT/'hardware/kicad/fan_ctrl_revB.kicad_sch'
    before=baseline.read_bytes();sha=hashlib.sha256(before).hexdigest()
    components,tree=load_design()
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='export_kicad_sch')
    ns=dict(COMPONENTS=components,KICAD_DIR=str(args.out),re=re,math=math,os=os)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'isolated_schematic','exec'),ns)
    schematic=Path(ns['export_kicad_sch']());text=schematic.read_text(encoding='utf8');sch=parse(text)
    count=0
    for parent in children(one(sch,'lib_symbols'),'symbol'):
        for unit in children(parent,'symbol'):
            assert re.fullmatch(re.escape(parent[1].split(':')[-1])+r'_\d+_\d+',unit[1]),unit[1]
            count+=1
    # Exact full S-expression equality after normalizing only unit names proves
    # no pin geometry, connection, field, UUID, or instance-layout drift.
    assert normalized(parse(before.decode('utf8')))==normalized(sch),'Unexpected change beyond cache unit names'
    validate(schematic,components)
    def run(name,argv):
        p=subprocess.run([str(args.cli),*map(str,argv)],capture_output=True,encoding='utf8',errors='replace')
        (args.out/(name+'.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf8')
        return p.returncode
    net=args.out/'native.net'
    net_rc=run('netlist',['sch','export','netlist','--output',net,schematic]);assert net_rc==0,net_rc
    native=parse(net.read_text(encoding='utf8'));actual={};nc=set()
    for n in children(one(native,'nets'),'net'):
        name=one(n,'name')[1];pins={(one(p,'ref')[1],one(p,'pin')[1]) for p in children(n,'node')}
        if name.startswith('unconnected-'):
            assert len(pins)==1;nc.update(pins)
        else:actual[name.removeprefix('/')]=pins
    wanted=defaultdict(set);wanted_nc=set()
    for c in components:
        if c['type']=='hole':continue
        for p in c['pads']:
            if p[3] in ('NC','',None):wanted_nc.add((c['ref'],str(p[0])))
            else:wanted[p[3]].add((c['ref'],str(p[0])))
    assert dict(wanted)==actual, 'Native netlist differs from intended circuit'
    assert wanted_nc==nc, 'Native NC pins differ'
    bad=args.out/'negative_cache_prefix.kicad_sch'
    bad.write_text(text.replace('C_Polarized_0_1','C_Pol_0_1',1),encoding='utf8')
    bad_rc=run('negative_prefix',['sch','export','netlist','--output',args.out/'negative.net',bad])
    assert bad_rc!=0,'Native parser accepted known invalid cache prefix'
    erc=args.out/'erc.json'
    erc_rc=run('erc',['sch','erc','--format','json','--severity-all','--exit-code-violations','--output',erc,schematic])
    assert erc_rc in (0,5) and erc.exists(),('ERC did not complete',erc_rc)
    report=json.loads(erc.read_text(encoding='utf8'));violations=[v for s in report['sheets'] for v in s['violations']]
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()==sha,'Production baseline was modified'
    result=dict(native_parse_pass=True,cache_unit_count=count,geometry_and_connections_unchanged=True,native_named_nets=len(actual),native_connected_pins=sum(map(len,actual.values())),native_nc_pins=len(nc),netlist_exit=net_rc,negative_prefix_exit=bad_rc,erc_exit=erc_rc,erc_pass=not violations,erc_violation_count=len(violations),erc_types=dict(Counter(v['type'] for v in violations)),baseline_sha256=sha,kicad_version=report.get('kicad_version'))
    (args.out/'native_regression_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=True,indent=2))
    print('Parser/netlist regression completed; ERC findings are NOT a passing electrical review.')

if __name__=='__main__':main()
