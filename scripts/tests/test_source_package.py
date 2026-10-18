"""Offline fixture tests; no VM, services or provider calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('source_package', Path(__file__).parents[1] / 'check-source-package.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SourcePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.write('README.md', b'Public fixture\n')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL)

    def write(self, name, data):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def commit(self):
        self.git('add', '-A')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')

    def test_clean_tree_and_valid_evidence_manifest(self):
        self.write('.env.example', b'API_KEY=\n')
        self.write('evidence/item.txt', b'observation\n')
        self.write('evidence/sha256-manifest.json', json.dumps({'item.txt': hashlib.sha256(b'observation\n').hexdigest()}).encode())
        self.commit()
        report = MODULE.audit(self.repo, 'HEAD')
        self.assertEqual(report['findings'], [])
        self.assertEqual(report['evidence_hashes_checked'], 1)
        self.assertFalse(report['working_tree_dirty'])

    def test_forbidden_paths_and_private_key_findings_are_redacted(self):
        marker = b'-----BEGIN ' + b'PRIVATE KEY-----'
        self.write('.env.local', b'local-only')
        self.write('private-export.json', b'{}')
        self.write('credential.txt', marker)
        self.commit()
        report = MODULE.audit(self.repo, 'HEAD')
        kinds = {x['kind'] for x in report['findings']}
        self.assertIn('private_key', kinds)
        self.assertIn('forbidden_package_path', kinds)
        self.assertNotIn(marker.decode(), json.dumps(report))

    def test_untracked_secret_is_not_packaged_but_dirty_state_is_visible(self):
        self.commit()
        self.write('untracked.txt', b'not included')
        report = MODULE.audit(self.repo, 'HEAD')
        self.assertTrue(report['working_tree_dirty'])
        self.assertNotIn('untracked.txt', [x['path'] for x in report['inventory']])

    def test_hash_mismatch(self):
        self.write('evidence/sha256-manifest.json', json.dumps({'missing.txt': '0' * 64}).encode())
        self.commit()
        self.assertIn('evidence_hash_mismatch_or_missing', {x['kind'] for x in MODULE.audit(self.repo, 'HEAD')['findings']})

    def test_manifest_path_traversal_rejected(self):
        self.write('evidence/sha256-manifest.json', json.dumps({'../README.md': '0' * 64}).encode())
        self.commit()
        self.assertIn('invalid_evidence_manifest', {x['kind'] for x in MODULE.audit(self.repo, 'HEAD')['findings']})

    def test_symlinks_rejected(self):
        (self.repo / 'link').symlink_to('README.md')
        self.commit()
        self.assertIn('unsupported_symlink_or_submodule', {x['kind'] for x in MODULE.audit(self.repo, 'HEAD')['findings']})

    def test_binary_content_is_scanned(self):
        self.write('binary.bin', b'\0' + b'-----BEGIN ' + b'PRIVATE KEY-----')
        self.commit()
        self.assertIn('private_key', {x['kind'] for x in MODULE.audit(self.repo, 'HEAD')['findings']})


if __name__ == '__main__':
    unittest.main()
