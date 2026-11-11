"""AST-only exact parts contract; never executes generator or router."""
import ast
import copy
from pathlib import Path
import unittest

TREE=ast.parse((Path(__file__).parent/'build_perfect_revB_v3.py').read_text(encoding='utf8'))
DATA={n.targets[0].id:ast.literal_eval(n.value) for n in TREE.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('NETS','COMPONENTS')}

def check(data):
    c={x['ref']:x for x in data['COMPONENTS']}
    dc=c['DC1']
    assert dc['mpn']=='1729128' and 'MKDSN' in dc['val'] and 'MKDSN' in dc['fp']
    assert dc['body_size_mm']==[10.16,8.15,10.0]
    assert dc['pads']==[('1',0.,0.,'+5V_RAW',2.6,1.3),('2',5.08,0.,'GND',2.6,1.3)]
    for ref,nets in [('MOTO1',['TB_AO1','TB_AO2']),('SPK1',['VOICE_SPK_P','VOICE_SPK_N'])]:
        x=c[ref]
        assert x['mpn']=='XH-2PA' and x['mfr']=='ZHOURI' and x['lcsc']=='C5258883'
        assert x['fp']=='SmartFan:ZHOURI_XH-2PA_P2.50mm_Y'
        assert x['pads']==[('1',0.,-1.25,nets[0],1.7,1.),('2',0.,1.25,nets[1],1.7,1.)]
        assert '设计选取非厂家推荐' in x['desc']
    assert 'MIC1' not in c
    nets=dict(data['NETS'])
    assert set(nets)==set(range(1,36))-{23,32}  # removed MIC input and non-existent encoder SW
    assert 'ENC_SW' not in nets.values()
    assert all(p[3]!='ENC_SW' for x in c.values() for p in x['pads'])
    assert nets[24]=='GEST_INT' and nets[33]=='+5V_ASR' and nets[35]=='ASR_TX1'
    assert 'VOICE_MIC_P' not in nets.values()
    assert all(p[3]!='VOICE_MIC_P' for x in c.values() for p in x['pads'])
    q=c['Q1']
    assert q['mpn']==q['val']=='2N3904-TA(RANGE:200-300)' and q['mfr']=='JSCJ'
    assert q['fp']=='SmartFan:TO-92_EBC_Wide_P2.54mm_Y_LeadFormed'
    assert '成形' in q['desc'] and '1=E 2=B 3=C' in q['desc']
    assert q['pads']==[('1',0.,-2.54,'GND',1.4,.8),('2',0.,0.,'BUZ_BASE',1.4,.8),('3',0.,2.54,'BUZ_DRV',1.4,.8)]

class PartsContract(unittest.TestCase):
    def test_exact_parts(self):check(DATA)
    def test_negative_old_pitch(self):
        bad=copy.deepcopy(DATA);x=next(c for c in bad['COMPONENTS'] if c['ref']=='MOTO1');p=list(x['pads'][0]);p[2]=-1.27;x['pads'][0]=tuple(p)
        with self.assertRaises(AssertionError):check(bad)
    def test_negative_restored_mic_net(self):
        bad=copy.deepcopy(DATA);bad['NETS'].append((23,'VOICE_MIC_P'))
        with self.assertRaises(AssertionError):check(bad)
    def test_negative_wrong_ebc(self):
        bad=copy.deepcopy(DATA);x=next(c for c in bad['COMPONENTS'] if c['ref']=='Q1');p=list(x['pads'][0]);p[3]='BUZ_DRV';x['pads'][0]=tuple(p)
        with self.assertRaises(AssertionError):check(bad)
    def test_negative_wrong_body(self):
        bad=copy.deepcopy(DATA);next(c for c in bad['COMPONENTS'] if c['ref']=='DC1')['body_size_mm'][1]=9.8
        with self.assertRaises(AssertionError):check(bad)

if __name__=='__main__':unittest.main(verbosity=2)
