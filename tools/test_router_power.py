"""Power-only synthetic routing and independent negative gates; no full build."""
import unittest
from obstacle_router import route_power_backbone, route_board
from verify_revb_power import audit_power
from verify_revb_connectivity import check_networks
from shapely.geometry import LineString,Point,box


def pad(ref,pin,x,y,n,w=1.7,h=1.,kind='tht'):
    return dict(ref=ref,pad=str(pin),x=x,y=y,nid=n,w=w,h=h,type=kind)

class PowerTests(unittest.TestCase):
    def setUp(self):
        self.names={1:'GND',2:'+5V_RAW',3:'+5V_FUSED',4:'+5V',6:'+5V_MCU'}
        self.pads=[pad('DC1',1,4,5,2),pad('F1',1,10,5,2,1.96,3.15,'smd'),
                   pad('F1',2,15,5,3,1.96,3.15,'smd'),
                   pad('DC1',2,4,10,1),pad('SERVO1',1,4,22,1),pad('SERVO1',2,8,22,4)]
        self.pads += [pad('Q_PWR',i,24,10+(i-1)*1.27,4,1.5,.6,'smd') for i in (1,2,3)]
        self.pads += [pad('Q_PWR',i,30,10+(8-i)*1.27,3,1.5,.6,'smd') for i in (5,6,7,8)]
        self.pads += [pad('Q_PWR',4,24,13.81,1,1.5,.6,'smd')]

    def test_power_wide_tree_and_thin_or_via_substitutions(self):
        tracks,report=route_power_backbone(self.pads,self.names,(0,0,40,30))
        result=audit_power(self.pads,tracks,[],self.names,report)
        self.assertTrue(result['passed'],result)
        self.assertFalse(result['thermal_certified'])
        self.assertEqual(report['via_count'],0)
        q=[r for r in report['terminals'] if r['ref']=='Q_PWR']
        self.assertEqual(len(q),7)
        self.assertTrue(all(r['escape_length_mm']<=2 and r['escape_width_mm']>=.5 for r in q))
        thin=[(*t[:4],.5,*t[5:]) for t in tracks]
        self.assertFalse(audit_power(self.pads,thin,[],self.names,report)['passed'])
        bottom=[(*t[:5],'B.Cu',t[6]) for t in tracks]
        fake_vias=[(p['x'],p['y'],.6,.3,p['nid']) for p in self.pads]
        self.assertFalse(audit_power(self.pads,bottom,fake_vias,self.names,report)['passed'])
        front=[(*t[:5],'F.Cu',t[6]) if t[6]==1 else t for t in tracks]
        self.assertFalse(audit_power(self.pads,front,[],self.names,report)['passed'])
        missing_bridge=[dict(p,type='smd') if p['ref']=='SERVO1' and p['nid']==1 else p for p in self.pads]
        self.assertFalse(audit_power(missing_bridge,tracks,[],self.names,report)['passed'])
        small_bridge=[dict(p,h=.3) if p['ref']=='SERVO1' and p['nid']==1 else p for p in self.pads]
        self.assertFalse(audit_power(small_bridge,tracks,[],self.names,report)['passed'])
        npth_bridge=[dict(p,type='hole') if p['ref']=='SERVO1' and p['nid']==1 else p for p in self.pads]
        self.assertFalse(audit_power(npth_bridge,tracks,[],self.names,report)['passed'])
        # Independently inspect all generated copper for actual foreign-net clearance.
        ap=[];conductors=[]
        for i,p in enumerate(self.pads):
            key=f'p{i}';layers=['F.Cu'] if p['type']=='smd' else ['F.Cu','B.Cu']
            ap.append(dict(id=key,net=p['nid'],layers=layers))
            g=box(p['x']-p['w']/2,p['y']-p['h']/2,p['x']+p['w']/2,p['y']+p['h']/2) if p['type']=='smd' else Point(p['x'],p['y']).buffer(p['w']/2)
            conductors.extend((key,p['nid'],l,g) for l in layers)
        for i,t in enumerate(tracks):conductors.append((f't{i}',t[6],t[5],LineString([t[:2],t[2:4]]).buffer(t[4]/2)))
        result=check_networks(ap,conductors,{})
        self.assertEqual(result['clearance_violation_count'],0,result)
        print('Power fixture',len(tracks),'tracks; seven SO8 terminals; zero vias; independent wide-tree and copper clearance passed')

    def test_integrated_router_preserves_power_tree(self):
        tracks,vias=route_board(self.pads,(0,0,40,30),net_names=self.names)
        self.assertTrue(any(t[4]>=2 for t in tracks))
        self.assertTrue(all(v[2]>=.6 for v in vias))

    def test_impossible_escape_fails_closed(self):
        self.pads += [pad('BLOCK',1,24,10,0,2,2,'smd')]
        with self.assertRaisesRegex(RuntimeError,'placement change required'):
            route_power_backbone(self.pads,self.names,(0,0,40,30))

if __name__=='__main__':unittest.main(verbosity=2)
