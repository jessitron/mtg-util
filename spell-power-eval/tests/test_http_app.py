import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from spell_power_eval.adapters.results_file import ResultsDirectory
from spell_power_eval.orchestration.http_app import make_server

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample_run.json")


class ServedRunsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        for name in ("20261001T100000Z.json", "20261002T090000Z.json"):
            shutil.copy(FIXTURE, os.path.join(self.directory, name))
        with open(os.path.join(self.directory, "notes.json"), "w") as f:
            f.write("{}")
        self.server = make_server(ResultsDirectory(self.directory), 0)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.directory)

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read()

    def test_lists_runs_newest_first_and_skips_other_files(self):
        status, body = self.get("/api/runs")
        runs = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual([r["file"] for r in runs], ["20261002T090000Z.json", "20261001T100000Z.json"])
        self.assertEqual(runs[0]["cards"], 9)
        self.assertIn("jev-score", runs[0]["arms"])

    def test_fetches_one_run(self):
        status, body = self.get("/api/runs/20261001T100000Z.json")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["cards"][0]["name"], "Lightning Bolt")

    def test_a_missing_run_is_404(self):
        self.assertEqual(self.get("/api/runs/20250101T000000Z.json")[0], 404)

    def test_a_bad_file_name_is_404_and_never_reaches_the_disk(self):
        for bad in ("notes.json", "..%2Fsample.json", "%2e%2e/%2e%2e/etc/passwd", "20261001T100000Z.json.bak", "20261001T100000Z.JSON"):
            self.assertEqual(self.get("/api/runs/" + bad)[0], 404, bad)

    def test_serves_the_page_from_disk(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"<html", body)

    def test_unknown_route_is_404(self):
        self.assertEqual(self.get("/nope")[0], 404)

    def test_an_empty_or_missing_results_directory_lists_nothing(self):
        self.assertEqual(ResultsDirectory(os.path.join(self.directory, "absent")).names(), [])


if __name__ == "__main__":
    unittest.main()
