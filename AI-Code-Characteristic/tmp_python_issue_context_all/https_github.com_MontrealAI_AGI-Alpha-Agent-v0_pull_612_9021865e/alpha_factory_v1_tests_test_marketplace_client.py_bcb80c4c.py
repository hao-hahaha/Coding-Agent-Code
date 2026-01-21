import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_marketplace_v1 import (
    MarketplaceClient,
    load_job,
    parse_args,
)


class _Handler(BaseHTTPRequestHandler):
    received_path = None
    received_body = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        type(self).received_body = self.rfile.read(length)
        type(self).received_path = self.path
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


def _start_server():
    server = HTTPServer(("localhost", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class MarketplaceClientTest(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "server"):
            self.server.shutdown()
            self.thread.join()
            self.server.server_close()

    def test_queue_job(self):
        self.server, self.thread = _start_server()
        host, port = self.server.server_address
        client = MarketplaceClient(host, port)
        job = {"agent": "foo"}
        resp = client.queue_job(job)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(_Handler.received_path, "/agent/foo/trigger")
        self.assertEqual(json.loads(_Handler.received_body.decode()), job)

    def test_missing_agent(self):
        client = MarketplaceClient()
        with self.assertRaises(ValueError):
            client.queue_job({})

    def test_load_job(self):
        path = Path("alpha_factory_v1/demos/alpha_agi_marketplace_v1/examples/sample_job.json")
        job = load_job(path)
        self.assertEqual(job["agent"], "finance")

    def test_parse_args_defaults(self):
        args = parse_args([])
        sample = (
            Path(__file__).resolve().parents[1]
            / "demos"
            / "alpha_agi_marketplace_v1"
            / "examples"
            / "sample_job.json"
        ).resolve()
        self.assertEqual(Path(args.job_file), sample)
        self.assertEqual(args.host, "localhost")
        self.assertEqual(args.port, 8000)


if __name__ == "__main__":
    unittest.main()

