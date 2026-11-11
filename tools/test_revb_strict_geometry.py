"""Fail-closed regression against actual frozen bad PCB/Gerbers; no production writes."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from strict_copper_geometry import strict_polygon, gerber_polygon, AmbiguousCopperGeometry
from shapely.geometry import Point
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/strict_geometry_review'
class StrictGeometryTests(unittest.TestCase):
    def test_simple_legal_shape(self):
        p=strict_polygon([(0,0),(4,0),(4,3),(0,3)],'test rectangle',require_ccw=True)
        self.assertEqual(p.area,12)
    def test_bowtie_rejected(self):
        with self.assertRaises(AmbiguousCopperGeometry):strict_polygon([(0,0),(2,2),(0,2),(2,0)])
    def test_weak_bridge_rejected_not_repaired(self):
        with self.assertRaises(AmbiguousCopperGeometry):
            strict_polygon([(0,0),(4,0),(4,4),(0,4),(0,0),(1,1),(1,2),(2,2),(2,1),(1,1),(0,0)])
    def test_negative_pcb_ring_not_assumed_additive(self):
        with self.assertRaises(AmbiguousCopperGeometry):strict_polygon([(0,0),(0,3),(4,3),(4,0)],require_ccw=True)
    def test_gerber_valid_cut_in_both_orientations(self):
        pts=[(0,0),(4,0),(4,4),(0,4),(0,1),(1,1),(1,2),(2,2),(2,1),(1,1),(0,1),(0,0)]
        a=gerber_polygon(pts);b=gerber_polygon(list(reversed(pts)))
        self.assertEqual(a.area,15);self.assertTrue(a.equals(b))
        self.assertFalse(a.covers(Point(1.5,1.5)))
        self.assertTrue(a.covers(Point(.5,.5)))
    def test_gerber_negative_island_and_independent_contours(self):
        a=gerber_polygon([(0,0),(0,1),(1,1),(1,0)])
        b=gerber_polygon([(2,0),(3,0),(3,1),(2,1)])
        u=unary_union([a,b]);self.assertEqual(u.area,2)
        self.assertTrue(u.covers(Point(.5,.5)));self.assertTrue(u.covers(Point(2.5,.5)))
        # A separate D02 contour inside another contour is UNION, not a hole.
        outer=gerber_polygon([(-1,-1),(4,-1),(4,2),(-1,2)])
        self.assertTrue(unary_union([outer,a]).equals(outer))
    def test_gerber_cross_and_diagonal_bridge_rejected(self):
        with self.assertRaises(AmbiguousCopperGeometry):gerber_polygon([(0,0),(2,2),(0,2),(2,0)])
        with self.assertRaises(AmbiguousCopperGeometry):
            gerber_polygon([(0,0),(4,0),(4,4),(0,4),(0,0),(1,1),(1,2),(2,2),(2,1),(1,1),(0,0)])
    def test_current_frozen_bad_baseline_rejected_all_three(self):
        OUT.mkdir(parents=True,exist_ok=True)
        for name in ('verify_revb_copper','validate_revB_gerber_geometry','verify_revb_manufacturing'):
            with self.subTest(checker=name):
                report=OUT/(name+'.json')
                p=subprocess.run([sys.executable,str(ROOT/'tools'/f'{name}.py'),'--report',str(report)],cwd=ROOT,capture_output=True,encoding='utf8',errors='replace')
                (OUT/(name+'.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf8')
                self.assertEqual(p.returncode,1,p.stdout+p.stderr)
                d=json.loads(report.read_text(encoding='utf8'))
                self.assertFalse(d['passed'])
                self.assertFalse(d['geometry_interpretation_pass'])
                self.assertEqual(d['failures'],['ambiguous_geometry'])
                print(name,d['errors'])

if __name__=='__main__':unittest.main(verbosity=2)
