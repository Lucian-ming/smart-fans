"""AST-only true copper geometry regression for wide-track clearance; no build."""
import ast
import math
from pathlib import Path
import unittest
import manifold3d as m3d
import numpy as np
from shapely.geometry import LineString, Polygon

SOURCE=Path(__file__).with_name('build_perfect_revB_v3.py')
class TrackCutoutTests(unittest.TestCase):
    def distance(self,angle,old=False):
        tree=ast.parse(SOURCE.read_text(encoding='utf8'))
        fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('copper_zone_boundary','compute_copper_zone')]
        if old:
            for n in ast.walk(fns[-1]):
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('c1','c2') for t in n.targets):
                    n.value.func.value.args[1]=ast.Constant(10)
            ast.fix_missing_locations(tree)
        end=(145+10*math.cos(angle),145+10*math.sin(angle))
        ns=dict(m3d=m3d,np=np,math=math,PAD_RECORDS=[],VIAS=[],TRACKS=[(145,145,*end,2.,'F.Cu',2)],OFFSET_X=100,OFFSET_Y=100,BOARD_W=95,BOARD_H=95,CORNER_R=3)
        exec(compile(ast.Module(body=fns,type_ignores=[]),str(SOURCE),'exec'),ns)
        plane=Polygon(ns['compute_copper_zone']('F.Cu')).buffer(0)
        copper=LineString([(145,145),end]).buffer(1.,quad_segs=2048)
        return plane.distance(copper)
    def test_64_sided_actual_cutout_all_angles(self):
        theoretical=1.3*math.cos(math.pi/64)-1.
        self.assertGreater(theoretical,.2984)
        distances=[self.distance(math.radians(a)) for a in (0,9,18,27,45,73,90,135)]
        print('64-sided track min clearance',min(distances),'analytic lower bound',theoretical)
        self.assertGreaterEqual(min(distances),theoretical-1e-6)
    def test_old_decagon_rejected(self):
        self.assertLess(self.distance(math.radians(18),old=True),.25)

if __name__=='__main__':unittest.main(verbosity=2)
