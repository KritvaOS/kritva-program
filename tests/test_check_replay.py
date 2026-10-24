"""--check must be deterministic: it replays the generation time recorded in consolidated_status.json."""
import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import make_root, run, write_sources  # noqa: E402


class CheckReplay(unittest.TestCase):
    def test_check_passes_later_even_when_sources_age_past_the_freshness_window(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r)
            later = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
            self.assertEqual(run(r, "--sources-dir", str(r / "sources"), "--now", later).returncode, 0)
            gen = json.loads((r / "v2/tracking/consolidated_status.json").read_text())["generated_at"]
            self.assertEqual(gen, later)
            # real time is earlier than the recorded generation time; a replay must not depend on it
            self.assertEqual(run(r, "--sources-dir", str(r / "sources"), "--check").returncode, 0)
            # an explicit --now still wins (and detects drift when freshness would differ)
            self.assertEqual(run(r, "--sources-dir", str(r / "sources"), "--check", "--now",
                                 (datetime.datetime.now(datetime.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")).returncode, 4)

    def test_check_detects_real_drift(self):
        with tempfile.TemporaryDirectory() as d:
            r = make_root(d)
            write_sources(r)
            self.assertEqual(run(r, "--sources-dir", str(r / "sources")).returncode, 0)
            p = r / "v2/tracking/STATUS_VIEW.md"
            p.write_text(p.read_text() + "\nedited by hand\n")
            self.assertEqual(run(r, "--sources-dir", str(r / "sources"), "--check").returncode, 4)


if __name__ == "__main__":
    unittest.main()
