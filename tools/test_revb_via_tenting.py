"""Independent synthetic real-Gerber positive/negative tests, no board generation."""
import tempfile
import unittest
from pathlib import Path
from validate_revB_schematic import parse
from validate_revB_gerber_geometry import audit_tented_masks

class TentingTests(unittest.TestCase):
    def audit(self, via_x=3.0, extra='', tent='false', diameter='1.1000'):
        pcb=parse(f'''(kicad_pcb (setup (pad_to_mask_clearance 0.05)
          (pcbplotparams (viasonmask {tent})))
          (footprint "test" (at 0 0)
           (pad "1" thru_hole circle (at 0 0) (size 1 1)
            (drill 0.5) (layers "*.Cu" "*.Mask")))
          (via (at {via_x} 0) (size 0.6) (drill 0.3)
           (layers "F.Cu" "B.Cu") (net 1)))''')
        with tempfile.TemporaryDirectory() as d:
            for ext in ('GTS','GBS'):
                Path(d,f'fan_ctrl_revB.{ext}').write_text(
                    '%FSLAX45Y45*%\n%MOMM*%\n%LPD*%\n'
                    f'%ADD10C,{diameter}*%\n%ADD11C,0.7000*%\n'
                    'D10*\nX0Y0D03*\n'+extra+'M02*\n')
            return audit_tented_masks(pcb,d)

    def test_clear_tent_pass(self):
        e,r=self.audit()
        self.assertEqual(e,[])
        self.assertFalse(r['fabricator_certified'])
        self.assertGreater(r['F.Mask']['minimum_hole_cover_mm'],.1)
    def test_pad_window_covers_via_hole_rejected(self):
        e,_=self.audit(via_x=.2)
        self.assertEqual(sum(v['kind']=='via_tent_cover_clearance' for v in e),2)
    def test_insufficient_cover_without_overlap_rejected(self):
        e,_=self.audit(via_x=.75)
        self.assertEqual(sum(v['kind']=='via_tent_cover_clearance' for v in e),2)
    def test_extra_via_window_rejected(self):
        e,_=self.audit(extra='D11*\nX300000Y0D03*\n')
        self.assertIn('mask_geometry_mismatch',[r['kind'] for r in e])
        self.assertIn('via_tent_cover_clearance',[r['kind'] for r in e])
    def test_wrong_pad_aperture_rejected(self):
        e,_=self.audit(diameter='1.2000')
        self.assertIn('mask_geometry_mismatch',[r['kind'] for r in e])
    def test_untented_pcb_rejected(self):
        e,_=self.audit(tent='true')
        self.assertIn('via_tenting_not_explicit',[r['kind'] for r in e])

if __name__=='__main__': unittest.main(verbosity=2)
