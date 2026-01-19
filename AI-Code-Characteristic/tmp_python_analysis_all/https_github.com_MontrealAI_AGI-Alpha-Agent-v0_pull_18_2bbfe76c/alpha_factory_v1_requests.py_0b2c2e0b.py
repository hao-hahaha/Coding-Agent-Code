"""Minimal requests shim for offline test environment."""
from urllib import request as _request
import json

class Response:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)

def get(url: str, **kwargs):
    with _request.urlopen(url) as resp:
        data = resp.read().decode()
        return Response(resp.getcode(), data)
