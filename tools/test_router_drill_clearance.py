"""Small synthetic-board regression tests; never execute the production generator."""
import math
import unittest
from shapely.geometry import LineString, Point
from obstacle_router import DrillRegistry, route_board, pad_geometry, LAYERS
from verify_revb_connectivity import check_networks


def pad(ref,x,y,net=7,kind='smd',w=.6,h=.6):
    return dict(ref=ref,pad='1',x=x,y=y,nid=net,type=kind,w=w,h=h)


class DrillTests(unittest.TestCase):
    def test_reported_same_net_overlap_rejected(self):
        r=DrillRegistry([])
        self.assertTrue(r.add(137.2,123.9,7))
        self.assertFalse(r.can_place(137.3,124.0,7))
        with self.assertRaises(ValueError):r.add(137.3,124.0,7)
        self.assertEqual(len(r.vias),1)

    def test_clearance_boundary_and_exact_reuse(self):
        r=DrillRegistry([])
        self.assertTrue(r.add(2.,2.,7))
        self.assertFalse(r.add(2.,2.,7))
        self.assertFalse(r.can_place(2.,2.,8))
        self.assertFalse(r.can_place(2.549,2.,7))
        self.assertTrue(r.can_place(2.55,2.,7))
        self.assertTrue(r.add(2.55,2.,7))
        self.assertEqual(len(r.vias),2)

    def test_tht_and_mount_holes_are_net_independent(self):
        for kind,net in [('tht',7),('tht',8),('hole',0)]:
            with self.subTest(kind=kind,net=net):
                r=DrillRegistry([pad('H',2.,2.,net,kind,w=3.,h=1.)])
                self.assertFalse(r.can_place(2.,2.,7))
                self.assertFalse(r.can_place(2.899,2.,7))
                self.assertFalse(r.can_place(2.9,2.,7))
                self.assertFalse(r.can_place(3.799,2.,7))
                self.assertTrue(r.can_place(3.8,2.,7))

    def test_mask_clearance_same_net_nc_and_transaction(self):
        for net in (0,7,8):
            r=DrillRegistry([pad('PAD',2.,2.,net,'smd',2.,1.)])
            self.assertFalse(r.can_place(3.299,2.,7))
            self.assertTrue(r.can_place(3.3,2.,7))
            self.assertFalse(r.can_place(2.,2.799,7))
            self.assertTrue(r.can_place(2.,2.8,7))
            self.assertEqual(r.first_conflict([(5.,5.),(3.299,2.)],7),(3.299,2.))
            self.assertEqual(r.vias,{})
            with self.assertRaises(ValueError):r.add(3.299,2.,7)
            self.assertTrue(r.add(3.3,2.,7))
            self.assertFalse(r.add(3.3,2.,7))
        # Circle diagonal must use outer copper diameter, not drill diameter.
        r=DrillRegistry([pad('TH',2.,2.,7,'tht',3.,.8)])
        self.assertFalse(r.can_place(2.+1.799/math.sqrt(2),2.+1.799/math.sqrt(2),7))
        self.assertTrue(r.can_place(2.+1.8/math.sqrt(2),2.+1.8/math.sqrt(2),7))

    def test_one_path_conflicts_are_transactional(self):
        r=DrillRegistry([])
        self.assertEqual(r.first_conflict([(2.,2.),(2.1,2.1)],7),(2.1,2.1))
        self.assertEqual(r.holes,[])
        self.assertIsNone(r.first_conflict([(2.,2.),(2.,2.),(2.6,2.)],7))
        self.assertEqual(r.vias,{})

    def test_synthetic_board_drills_copper_and_connectivity(self):
        # An NC SMD wall forces layer changes. Four nearby same-net terminals
        # exercise successive paths; two drilled obstacles exercise both layers.
        pads=[pad('A',2,3),pad('B',8,3),pad('C',2,3.4),pad('D',8,3.4),
              pad('E',2,7,8),pad('F',8,7,8),
              pad('WALL',5,5,0,'smd',1.,10.),
              pad('TH',3,5,0,'tht',1.5,.8),
              pad('MH',7,4.5,0,'hole',1.2,1.)]
        tracks,vias=route_board(pads,bounds=(0.,0.,10.,10.))
        self.assertGreaterEqual(len(vias),2)
        self.assertEqual(len(vias),len({v[:2] for v in vias}))
        # Independent numeric check, not the registry under test.
        holes=[(p['x'],p['y'],p['h']) for p in pads if p['type']!='smd']
        for x,y,size,drill,net in vias:
            for p in pads:
                copper=pad_geometry(p)
                self.assertGreaterEqual(copper.distance(Point(x,y))-.05-drill/2,.10-1e-8)
            for hx,hy,hd in holes:
                self.assertGreaterEqual(math.hypot(x-hx,y-hy)-(drill+hd)/2,.25-1e-9)
            holes.append((x,y,drill))
        audit_pads=[];conductors=[]
        for p in pads:
            ls=LAYERS if p['type']!='smd' else LAYERS[:1]
            audit_pads.append(dict(id=p['ref'],net=p['nid'],layers=ls))
            conductors.extend((p['ref'],p['nid'],l,pad_geometry(p)) for l in ls)
        for i,(x1,y1,x2,y2,width,layer,net) in enumerate(tracks):
            conductors.append((f'track{i}',net,layer,LineString([(x1,y1),(x2,y2)]).buffer(width/2)))
        without_vias=conductors.copy()
        for i,(x,y,size,drill,net) in enumerate(vias):
            conductors.extend((f'via{i}',net,l,Point(x,y).buffer(size/2)) for l in LAYERS)
        result=check_networks(audit_pads,conductors,{})
        self.assertEqual(result['clearance_violation_count'],0,result)
        self.assertEqual(result['disconnected_net_count'],0,result)
        # Negative control: dropping the emitted interlayer bridges must fail.
        result=check_networks(audit_pads,without_vias,{})
        self.assertGreater(result['disconnected_net_count'],0,result)


if __name__=='__main__':
    unittest.main(verbosity=2)
