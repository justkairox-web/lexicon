"""Lexicon cloud sync: merges the phone's word list with the copy in Upstash Redis.

Uses the same env vars Jarvis already has: JARVIS_PASSWORD, KV_REST_API_URL, KV_REST_API_TOKEN.
"""
import hmac
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import unquote

KEY = "lexicon:words"
MAX_ITEMS = 5000
MAX_BODY = 1_500_000


def redis(cmd):
    req = urllib.request.Request(
        os.environ["KV_REST_API_URL"],
        data=json.dumps(cmd).encode(),
        headers={
            "Authorization": "Bearer " + os.environ["KV_REST_API_TOKEN"],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())["result"]


def clean(raw):
    """Keep only well-formed items with sane sizes."""
    out = []
    for i in raw if isinstance(raw, list) else []:
        if not isinstance(i, dict) or not isinstance(i.get("id"), str):
            continue
        out.append({
            "id": i["id"][:40],
            "w": str(i.get("w", ""))[:120],
            "m": str(i.get("m", ""))[:2000],
            "t": int(i.get("t") or 0),
            "u": int(i.get("u") or 0),
            "b": int(i.get("b") or 0),
            "r": int(i.get("r") or 0),
            "x": int(i.get("x") or 0),
            **({"d": 1} if i.get("d") else {}),
        })
    return out[:MAX_ITEMS]


def merge(a, b):
    best = {}
    for i in a + b:
        cur = best.get(i["id"])
        if cur is None or i["u"] > cur["u"]:
            best[i["id"]] = i
    return list(best.values())


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        expected = os.environ.get("JARVIS_PASSWORD", "")
        given = unquote(self.headers.get("x-dict-password", ""))
        if not expected or not hmac.compare_digest(given.encode(), expected.encode()):
            return self._send(401, {"error": "unauthorized"})
        try:
            length = int(self.headers.get("content-length") or 0)
            if length > MAX_BODY:
                return self._send(413, {"error": "too large"})
            body = json.loads(self.rfile.read(length) or b"{}")
            incoming = clean(body.get("items", []))
            stored = redis(["GET", KEY])
            merged = merge(clean(json.loads(stored)) if stored else [], incoming)
            redis(["SET", KEY, json.dumps(merged, separators=(",", ":"))])
            return self._send(200, {"items": merged})
        except Exception as e:  # keep the app working offline-first; it will retry
            return self._send(500, {"error": str(e)[:200]})
