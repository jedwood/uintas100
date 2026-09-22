#!/usr/bin/env python3
"""Static server for the Uintas repo with fault-injection toggles, so the
service-worker's offline behaviour can be exercised end to end:

  /__ctl?version=B        serve service-worker.js with CACHE_NAME = uintas-vB
  /__ctl?fail=PATH        that path answers 503 (comma-separated; '' clears)
  /__ctl?portal=1|0       every non-control GET answers 200 text/html (captive portal)
  /__ctl?offline=1|0      every non-control request has its connection dropped
  /__ctl?status           JSON of the current toggles
"""
import json, os, re, socket, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = sys.argv[1]
PORT = int(sys.argv[2])
STATE = {'version': None, 'fail': set(), 'portal': False, 'offline': False}


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/__ctl':
            q = parse_qs(u.query, keep_blank_values=True)
            if 'version' in q: STATE['version'] = q['version'][0] or None
            if 'fail' in q: STATE['fail'] = set(p for p in q['fail'][0].split(',') if p)
            if 'portal' in q: STATE['portal'] = q['portal'][0] == '1'
            if 'offline' in q: STATE['offline'] = q['offline'][0] == '1'
            if 'log' in q:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results.txt'), 'a') as f: f.write(q['log'][0] + '\n')
            body = json.dumps({k: (sorted(v) if isinstance(v, set) else v) for k, v in STATE.items()}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
            return
        if STATE['offline']:
            # Real "no network": reset the connection without a response.
            try:
                self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x01\x00\x00\x00\x00\x00\x00\x00')
            except Exception:
                pass
            self.close_connection = True
            self.connection.close()
            return
        rel = u.path.lstrip('/')
        if STATE['portal']:
            body = b'<html><body><h1>Trailhead Motel Wi-Fi</h1><p>Log in to continue</p></body></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if rel in STATE['fail']:
            self.send_error(503, 'injected failure')
            return
        if rel == 'service-worker.js' and STATE['version']:
            src = open(os.path.join(ROOT, 'service-worker.js'), 'rb').read()
            src = re.sub(rb"const CACHE_NAME = 'uintas-v[^']*';",
                         b"const CACHE_NAME = 'uintas-v" + STATE['version'].encode() + b"';", src, count=1)
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(src)))
            self.end_headers()
            self.wfile.write(src)
            return
        return super().do_GET()

    def end_headers(self):
        # Never let the HTTP cache mask what the service worker does.
        if not any(h.lower() == 'cache-control' for h in self._headers_buffer_names()):
            self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def _headers_buffer_names(self):
        try:
            return [l.decode('latin-1').split(':', 1)[0] for l in self._headers_buffer if b':' in l]
        except Exception:
            return []


if __name__ == '__main__':
    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
