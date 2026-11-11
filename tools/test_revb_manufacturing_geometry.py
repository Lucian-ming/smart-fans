"""AST-isolated manufacturing regression; no routing or production build."""
import ast
import copy
import math
import os
from pathlib import Path
import re
import tempfile
import unittest
import manifold3d as m3d
import numpy as np
from shapely.geometry import Polygon, box
import sexpdata
from validate_revB_schematic import validate

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tools/build_perfect_revB_v3.py'

def children(node,name):
    return [n for n in node if isinstance(n,list) and n and str(n[0])==name]

def one(node,name):
    return children(node,name)[0]

class ManufacturingTests(unittest.TestCase):
    def setUp(self):
        tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
        self.ns=dict(math=math,os=os,re=re,m3d=m3d,np=np)
        constants={'COMPONENTS','NETS','BOARD_W','BOARD_H','CORNER_R','OFFSET_X','OFFSET_Y'}
        for n in tree.body:
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:
                self.ns[n.targets[0].id]=ast.literal_eval(n.value)
        fns={'get_3d_model','build_safe_silkscreen','copper_zone_boundary','compute_copper_zone','export_kicad_pcb','export_kicad_sch'}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in fns],type_ignores=[]),str(SOURCE),'exec'),self.ns)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ns.update(KICAD_DIR=self.tmp.name,NET_MAP={name:nid for nid,name in self.ns['NETS']},TRACKS=[],VIAS=[],PAD_RECORDS=[])

    def test_reference_pad_dimensions_and_rotation(self):
        for ref,filename,angle in [('D3','D_SOD-123',180)]:
            comp=next(c for c in self.ns['COMPONENTS'] if c['ref']==ref)
            lib=sexpdata.loads((ROOT/f'artifacts/footprint_reference/{filename}.kicad_mod').read_text(encoding='utf-8'))
            expected=[]
            for p in children(lib,'pad'):
                x,y=map(float,one(p,'at')[1:3]);w,h=map(float,one(p,'size')[1:3])
                if angle==90:x,y,w,h=y,-x,h,w
                else:x,y=-x,-y
                expected.append((str(p[1]),x,y,w,h))
            actual=[(p[0],p[1],p[2],p[4],p[5]) for p in comp['pads']]
            self.assertEqual(sorted(actual),sorted(expected),ref)
            self.assertEqual(comp['model_rotation_z'],angle)
            self.assertTrue(comp['fp'].startswith('SmartFan:'))
        u3=next(c for c in self.ns['COMPONENTS'] if c['ref']=='U3')
        # TI DCY recommended rectangular land envelope; evidence: tlv1117lv.pdf p23.
        self.assertEqual(u3['pads'], [('1',-2.3,2.9,'GND',.95,2.15),('2',0.,2.9,'+3.3V',.95,2.15),('3',2.3,2.9,'+5V',.95,2.15),('2',0.,-2.9,'+3.3V',3.25,2.15)])
        self.assertEqual((u3['val'],u3['mpn'],u3['lcsc'],u3['mfr']), ('TLV1117LV33DCYR','TLV1117LV33DCYR','C15578','Texas Instruments'))
        self.assertEqual(u3['model_rotation_z'],90)
        self.assertEqual([p[3] for p in u3['pads'] if p[0]=='2'],['+3.3V','+3.3V'])

    def test_rounded_boundary_rejects_old_square_corner(self):
        boundary=Polygon(self.ns['copper_zone_boundary']())
        board=box(103,103,192,192).buffer(3,quad_segs=4096)
        self.assertAlmostEqual(boundary.bounds[0],101)
        self.assertGreaterEqual(boundary.distance(board.boundary),1-1e-6)
        old=box(101,101,194,194)
        self.assertLess(old.distance(board.boundary),.18)
        self.assertGreater(old.difference(boundary).area,3.)
        filled=Polygon(self.ns['compute_copper_zone']('F.Cu'))
        self.assertLess(filled.symmetric_difference(boundary).area,1e-5)

    def test_pcb_layers_models_and_zone_boundary(self):
        boundary=self.ns['copper_zone_boundary']()
        self.ns['KEYHOLE_POLYS']={l:boundary for l in ('F.Cu','B.Cu')}
        pcb=sexpdata.loads(Path(self.ns['export_kicad_pcb']()).read_text(encoding='utf-8'))
        layers={n[1] for n in one(pcb,'layers')[1:]}
        self.assertTrue({'F.Paste','B.Paste','F.Fab','B.Fab','Cmts.User','Edge.Cuts'}<=layers)
        for f in children(pcb,'footprint'):
            ref=next(p[2] for p in children(f,'property') if p[1]=='Reference')
            if ref in ('U3','D1','D2','D3'):
                rotation=one(one(f,'model'),'rotate')
                self.assertEqual(one(rotation,'xyz')[3],90 if ref=='U3' else 180)
        for zone in children(pcb,'zone'):
            pts=one(one(zone,'polygon'),'pts')[1:]
            actual=Polygon([(float(p[1]),float(p[2])) for p in pts])
            self.assertLess(actual.symmetric_difference(Polygon(boundary)).area,1e-6)

    def test_schematic_duplicate_physical_pin_is_single_electrical_pin(self):
        result=validate(Path(self.ns['export_kicad_sch']()),self.ns['COMPONENTS'])
        self.assertEqual(result['pins'],sum(len({p[0] for p in c['pads']}) for c in self.ns['COMPONENTS'] if c['type']!='hole'))
        self.assertEqual(result['errors'],[])

    def test_duplicate_pin_different_net_is_rejected(self):
        self.ns['COMPONENTS']=copy.deepcopy(self.ns['COMPONENTS'])
        u3=next(c for c in self.ns['COMPONENTS'] if c['ref']=='U3')
        p=list(u3['pads'][-1]);p[3]='GND';u3['pads'][-1]=tuple(p)
        with self.assertRaisesRegex(AssertionError,'conflicting pad nets'):
            self.ns['export_kicad_sch']()

if __name__=='__main__':
    unittest.main(verbosity=2)
