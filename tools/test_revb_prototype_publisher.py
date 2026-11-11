"""Synthetic publisher preflight tests; never calls main or writes a delivery directory."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import publish_revb_pcb_prototype as p

class PublishContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in p.REQUIRED_HASHES | {x[0] for x in p.PAIRS}:
            target = self.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(name.encode())
        with zipfile.ZipFile(self.root/p.PAIRS[2][0], 'w') as z:
            for name in sorted(p.GERBER_NAMES):
                z.writestr(name, (self.root/(p.GERBER_DIR+name)).read_bytes())
        self.summary = {'automatic_checks_pass':True, 'checks':[{'name':n,'exit_code':0} for n in sorted(p.REQUIRED_CHECKS)], 'sha256':{n:p.digest(self.root/n) for n in p.REQUIRED_HASHES}}
        self.review = {'status':'reviewed_prototype_only', 'scope':'pcb_prototype_only', 'unresolved_limits':['Synthetic test only'], 'source_sha256':{n:p.digest(self.root/n) for n,_ in p.PAIRS}}
    def run_check(self):
        data = json.dumps(self.summary).encode()
        self.review['validation_summary_sha256'] = p.sha(data)
        return p.validate_release(self.root, data, self.review)
    def test_valid(self):
        self.assertEqual(len(self.run_check()), 6)
    def test_missing_or_duplicate_check(self):
        self.summary['checks'][0] = copy.deepcopy(self.summary['checks'][1])
        with self.assertRaises(ValueError): self.run_check()
    def test_nonzero_check_even_with_pass_flag(self):
        self.summary['checks'][0]['exit_code'] = 1
        with self.assertRaises(ValueError): self.run_check()
    def test_missing_gerber_hash(self):
        del self.summary['sha256'][p.GERBER_DIR+'fan_ctrl_revB.GBO']
        with self.assertRaises(ValueError): self.run_check()
    def test_missing_document_review(self):
        del self.review['source_sha256'][p.PAIRS[4][0]]
        with self.assertRaises(ValueError): self.run_check()
    def test_changed_document(self):
        (self.root/p.PAIRS[5][0]).write_bytes(b'changed after review')
        with self.assertRaises(ValueError): self.run_check()
    def test_changed_pcb(self):
        (self.root/p.PAIRS[0][0]).write_bytes(b'old pcb')
        with self.assertRaises(ValueError): self.run_check()
    def test_wrong_scope(self):
        self.review['scope'] = 'full_production'
        with self.assertRaises(ValueError): self.run_check()
    def test_old_summary_binding(self):
        self.review['validation_summary_sha256'] = '0'*64
        with self.assertRaises(ValueError): p.validate_release(self.root,json.dumps(self.summary).encode(),self.review)
    def test_reviewed_archive_still_must_match_verified_gerbers(self):
        with zipfile.ZipFile(self.root/p.PAIRS[2][0], 'w') as z:
            for name in p.GERBER_NAMES: z.writestr(name,b'stale')
        self.review['source_sha256'][p.PAIRS[2][0]] = p.digest(self.root/p.PAIRS[2][0])
        with self.assertRaises(ValueError): self.run_check()
    def test_windows_hash_keys(self):
        self.summary['sha256'] = {k.replace('/', '\\'):v for k,v in self.summary['sha256'].items()}
        self.assertEqual(len(self.run_check()),6)

if __name__ == '__main__': unittest.main(verbosity=2)
