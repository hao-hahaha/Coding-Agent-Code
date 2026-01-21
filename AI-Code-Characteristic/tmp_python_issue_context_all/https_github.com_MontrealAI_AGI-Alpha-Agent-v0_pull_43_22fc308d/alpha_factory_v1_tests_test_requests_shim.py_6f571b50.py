import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest

from alpha_factory_v1 import requests


def start_server(status=200, body=b"ok"):
    class Handler(BaseHTTPRequestHandler):
        received_body = None
        received_headers = None

        def do_GET(self):
            type(self).received_headers = dict(self.headers)
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            type(self).received_body = self.rfile.read(length)
            type(self).received_headers = dict(self.headers)
            self.send_response(status)
            self.end_headers()
            self.wfile.write(type(self).received_body)

    server = HTTPServer(("localhost", 0), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    url = f"http://{server.server_address[0]}:{server.server_address[1]}"
    return server, t, Handler, url


class RequestsShimTest(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "server"):
            self.server.shutdown()
            self.thread.join()
            self.server.server_close()

    def test_get_ok(self):
        self.server, self.thread, H, url = start_server()
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "ok")
        self.assertIsNone(H.received_body)
        self.assertIn("Host", H.received_headers)
        self.assertIn("Server", resp.headers)

    def test_post_json(self):
        self.server, self.thread, H, url = start_server()
        payload = {"x": 1}
        resp = requests.post(url, json=payload)
        self.assertEqual(resp.json(), payload)
        self.assertEqual(H.received_body, json.dumps(payload).encode())
        self.assertEqual(H.received_headers.get("Content-Type"), "application/json")
        self.assertIn("Server", resp.headers)

    def test_post_bytes(self):
        self.server, self.thread, H, url = start_server()
        payload = b"binary"
        resp = requests.post(url, data=payload)
        self.assertEqual(resp.text, payload.decode())
        self.assertEqual(H.received_body, payload)
        self.assertEqual(
            H.received_headers.get("Content-Type"),
            "application/x-www-form-urlencoded",
        )
        self.assertIn("Server", resp.headers)

    def test_raise_for_status(self):
        self.server, self.thread, H, url = start_server(status=404)
        resp = requests.get(url)
        with self.assertRaises(RuntimeError):
            resp.raise_for_status()


if __name__ == "__main__":
    unittest.main()
