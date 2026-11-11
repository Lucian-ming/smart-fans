"""AST-only silk regression; does not route or publish production artifacts."""
import ast
import math
import os
from pathlib import Path
import re
import tempfile
import unittest
import zipfile
import sexpdata
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from gerbonara import GerberFile
from verify_revb_manufacturing import geom

ROOT=Path(__file__).resolve().parents[1]

def ch(n,key):return [v for v in n if isinstance(v,list) and v and str(v[0])==key]
def one(n,key):return ch(n,key)[0]

class SilkTests(unittest.TestCase):
    def setUp(self):
        tree=ast.parse((ROOT/'tools/build_perfect_revB_v3.py').read_text(encoding='utf8'))
        self.ns=dict(math=math,os=os,re=re,zipfile=zipfile)
        for n in tree.body:
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'COMPONENTS','NETS','BOARD_W','BOARD_H','OFFSET_X','OFFSET_Y','CORNER_R'}:
                self.ns[n.targets[0].id]=ast.literal_eval(n.value)
        names={'copper_zone_boundary','build_safe_silkscreen','export_gerber_and_drill','export_kicad_pcb','get_3d_model'}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'isolated_silk','exec'),self.ns)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ns.update(KICAD_DIR=self.tmp.name,FAB_DIR=self.tmp.name,DOWNLOAD_DIR=self.tmp.name,TRACKS=[],VIAS=[(127,105,.6,.3,7),(152,112,.6,.3,8)])
        self.ns['NET_MAP']={s:n for n,s in self.ns['NETS']}
        self.ns['PAD_RECORDS']=[dict(ref=c['ref'],pad=p[0],x=100+c['x']+p[1],y=100+c['y']+p[2],w=p[4],h=p[5],type=c['type'],nid=self.ns['NET_MAP'].get(p[3],0)) for c in self.ns['COMPONENTS'] for p in c['pads']]
        self.ns['KEYHOLE_POLYS']={l:self.ns['copper_zone_boundary']() for l in ('F.Cu','B.Cu')}

    def test_exported_mask_clearance_all_refs_and_pcb_equality(self):
        rows=self.ns['build_safe_silkscreen']()
        refs={c['ref'] for c in self.ns['COMPONENTS']}
        self.assertEqual({r['ref'] for r in rows if r['kind']=='TEXT'},refs)
        self.assertEqual({r['ref'] for r in rows if r['kind']=='BORDER'},refs)
        self.assertTrue(all(len(r['segments'])>=4 for r in rows if r['kind']!='BORDER'))
        for row in rows:
            if row['kind']=='BORDER':
                # Safe clipping may leave three sides; reject a lone/collinear line.
                self.assertGreaterEqual(len(row['segments']),2,row['ref'])
                self.assertTrue(any(abs(s[2]-s[0])>1e-5 for s in row['segments']),row['ref'])
                self.assertTrue(any(abs(s[3]-s[1])>1e-5 for s in row['segments']),row['ref'])
        notices=[r for r in rows if r['kind']=='NOTICE']
        texts={r['text'] for r in notices}
        self.assertTrue({'5V ONLY','DC1 1:+ 2:GND','JP_USB OPEN BEFORE USB'} <= texts)
        if 'JP_ASR' in refs:self.assertIn('USB: OPEN PWR TX RX',texts)
        if 'J_OLED' in refs:
            self.assertIn('OLED L>R: SDA SCL VCC GND',texts)
            row=next(r for r in notices if r['text']=='OLED L>R: SDA SCL VCC GND')
            pts=[(s[i],s[i+1]) for s in row['segments'] for i in (0,2)]
            print('OLED notice board-global bounds mm:',min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts))
        for comp in self.ns['COMPONENTS']:
            ref=comp['ref']
            if ref.startswith(('J_','JP_')) or ref in ('MOTO1','SERVO1','SPK1','MIC1'):
                candidates=[t for t in texts if t.startswith(ref+' P1 ')]
                self.assertEqual(len(candidates),1,ref)
                p=next(p for p in comp['pads'] if p[0]=='1')
                xs=[q[1] for q in comp['pads']];ys=[q[2] for q in comp['pads']]
                if max(xs)-min(xs)>max(ys)-min(ys):
                    expected='LEFT' if p[1]==min(xs) else 'RIGHT'
                else:expected='TOP' if p[2]==min(ys) else 'BOTTOM'
                self.assertEqual(candidates[0],ref+' P1 '+expected)
            if ref.startswith('D') and ref!='DC1':
                self.assertEqual(len([t for t in texts if t.startswith(ref+' K=1 ')]),1)
        # Each complete glyph contour must survive conversion, not just a comment.
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties
        for row in notices:
            polys=TextPath((0,0),row['text'],size=1.40,prop=FontProperties(family='DejaVu Sans',weight='bold')).to_polygons()
            count=sum(sum(tuple(a)!=tuple(b) for a,b in zip(poly,poly[1:])) for poly in polys)
            self.assertEqual(len(row['segments']),count,row['text'])
        self.ns['export_gerber_and_drill']()
        gto=(Path(self.tmp.name)/'fan_ctrl_revB.GTO').read_text()
        notice_blocks=re.findall(r'G04 REF (\S+) NOTICE\*\n(.*?)(?=G04 REF |M02\*)',gto,re.S)
        self.assertEqual(len(notice_blocks),len(notices))
        for (ref,block),row in zip(notice_blocks,notices):
            self.assertEqual(ref,row['ref'])
            self.assertEqual(block.count('D01*'),len(row['segments']))
        mask=unary_union([geom(o) for o in GerberFile.open(Path(self.tmp.name)/'fan_ctrl_revB.GTS').objects])
        silk=unary_union([geom(o) for o in GerberFile.open(Path(self.tmp.name)/'fan_ctrl_revB.GTO').objects])
        self.assertLess(silk.intersection(mask).area,1e-8)
        self.assertGreaterEqual(silk.distance(mask),.1-1e-6)
        pcb=sexpdata.loads(Path(self.ns['export_kicad_pcb']()).read_text(encoding='utf8'))
        pcb_segments=[]
        for line in ch(pcb,'gr_line'):
            if one(line,'layer')[1]=='F.SilkS':
                a=one(line,'start')[1:];b=one(line,'end')[1:]
                pcb_segments.append(LineString([a,b]).buffer(float(one(line,'width')[1])/2,quad_segs=32))
        pcb_silk=unary_union(pcb_segments)
        self.assertLess(pcb_silk.symmetric_difference(silk).area,1e-6)
        print('Silk refs',len(refs),'segments',sum(len(r['segments']) for r in rows),'mask overlap',silk.intersection(mask).area,'min gap',silk.distance(mask))
        # The gate must reject a deliberate line crossing a real mask opening.
        p=self.ns['PAD_RECORDS'][0]
        bad=LineString([(p['x']-.1,p['y']),(p['x']+.1,p['y'])]).buffer(.075)
        self.assertGreater(bad.intersection(mask).area,1e-8)

    def test_unplaceable_reference_fails_not_silently_deleted(self):
        self.ns['COMPONENTS']=[dict(ref='BLOCK',x=47.5,y=47.5,type='smd',pads=[('1',0,0,'GND',100,100)])]
        with self.assertRaisesRegex(RuntimeError,'No safe readable'):
            self.ns['build_safe_silkscreen']()

    def test_unplaceable_notice_fails_not_cropped(self):
        self.ns['COMPONENTS']=[dict(ref='DC1',x=5,y=5,type='tht',pads=[('1',-1,0,'+5V_RAW',.2,.1),('2',1,0,'GND',.2,.1)])]
        self.ns['VIAS']=[]
        self.ns['copper_zone_boundary']=lambda *args: [(100,100),(110,100),(110,110),(100,110)]
        with self.assertRaisesRegex(RuntimeError,'No safe readable silkscreen placement for DC1: DC1 1:'):
            self.ns['build_safe_silkscreen']()

    def test_optional_asr_notice_is_dynamic(self):
        self.ns['COMPONENTS']=[c for c in self.ns['COMPONENTS'] if not c['ref'].startswith('JP_ASR')]
        rows=self.ns['build_safe_silkscreen']()
        self.assertNotIn('USB: OPEN PWR TX RX',{r.get('text') for r in rows})

if __name__=='__main__':unittest.main(verbosity=2)
