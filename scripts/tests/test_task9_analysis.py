"""Offline helper contracts; no models, application services or candidate execution."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("task9_analysis", ROOT / "scripts/analyze-task9-sanitized.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PAYLOAD = ROOT / "tasks/reports/evidence/task-09-observed-comparison/payload"


class Task9AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.payload = Path(self.tmp.name) / "payload"
        shutil.copytree(PAYLOAD, self.payload)

    def refresh_hash(self, relative):
        manifest = self.payload / "SHA256-MANIFEST.json"
        values = MODULE.load(manifest)
        values[relative] = MODULE.digest(self.payload / relative)
        manifest.write_text(json.dumps(values))

    def test_valid_records_and_pairs(self):
        result = MODULE.analyze(self.payload)
        self.assertEqual(result["summary"]["native_final_responses"], 2)
        self.assertEqual(result["summary"]["permission_stopped"], 2)
        self.assertEqual(result["summary"]["frozen_runtime_check_passes"], 4)
        self.assertTrue(all(p["input_graph_higher"] for p in result["pairs"]))
        self.assertEqual({r["mcp_calls"] for r in result["trials"]}, {0, 1})

    def test_tampered_original_bytes_fail(self):
        with (self.payload / "trial-01/acceptance.log").open("a") as handle:
            handle.write("modified")
        with self.assertRaises(AssertionError):
            MODULE.analyze(self.payload)

    def test_changed_usage_with_refreshed_file_hash_still_fails(self):
        path = self.payload / "trial-01/receipt.json"
        values = MODULE.load(path)
        values["usage_categories"]["input"] += 1
        path.write_text(json.dumps(values))
        self.refresh_hash("trial-01/receipt.json")
        with self.assertRaises(AssertionError):
            MODULE.analyze(self.payload)

    def test_duplicate_trial_with_refreshed_file_hash_still_fails(self):
        path = self.payload / "trials.csv"
        rows = path.read_text().splitlines()
        rows[2] = rows[1]
        path.write_text("\n".join(rows) + "\n")
        self.refresh_hash("trials.csv")
        with self.assertRaises(AssertionError):
            MODULE.analyze(self.payload)

    def test_manifest_path_escape_refused(self):
        path = self.payload / "SHA256-MANIFEST.json"
        values = MODULE.load(path)
        first = next(iter(values))
        value = values.pop(first)
        values["../outside"] = value
        path.write_text(json.dumps(values))
        with self.assertRaises(AssertionError):
            MODULE.analyze(self.payload)


if __name__ == "__main__":
    unittest.main()