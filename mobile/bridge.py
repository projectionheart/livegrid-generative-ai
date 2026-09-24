"""Opt-in phone controller bridge. Standard library only; engine stays on loopback."""
import argparse
import hmac
import json
import math
import secrets
import socket
import struct
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT.parent / 'docs' / 'mobile'
PAGES = 'https://projectionheart.github.io'

def osc(address, value):
    def string(s):
        b = s.encode() + b'\0'
        return b + b'\0' * (-len(b) % 4)
    return string(address) + string(',f') + struct.pack('>f', float(value))

def validate(data):
    if not isinstance(data, dict) or not data:
        raise ValueError('Expected controls')
    result = {}
    for k, v in data.items():
        if k == 'prompt':
            if not isinstance(v, str) or not v.strip() or len(v) > 2000:
                raise ValueError('Prompt must contain 1–2000 characters')
            result[k] = v.strip()
        elif k == 'layout':
            if v not in ('mosaic', 'repeat'): raise ValueError('Invalid layout')
            result[k] = v
        elif k in ('freeze', 'blackout', 'calibrate'):
            if type(v) is not bool: raise ValueError('Invalid switch')
            result[k] = v
        elif k in ('speed', 'gap', 'brightness', 'x', 'y'):
            lo, hi = {'speed': (.005, .5), 'gap': (0, 30)}.get(k, (0, 1))
            if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
                raise ValueError('Control out of range: ' + k)
            result[k] = int(v) if k == 'gap' else v
        else: raise ValueError('Unknown control: ' + k)
    return result

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def origin_ok(self):
        origin = self.headers.get('Origin')
        # Local controller origin must match the request host. Hosted controller is explicit.
        return origin is None or origin == PAGES or origin == 'http://' + self.headers.get('Host', '') or origin == self.server.public_origin
    def respond(self, code, data, kind='application/json'):
        if not isinstance(data, bytes): data = json.dumps(data).encode()
        self.send_response(code)
        origin = self.headers.get('Origin')
        if origin and self.origin_ok():
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass
    def authorized(self):
        return self.origin_ok() and hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + self.server.token)
    def do_OPTIONS(self):
        if not self.origin_ok(): return self.respond(403, {'error': 'Origin rejected'})
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', self.headers.get('Origin', PAGES))
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Vary', 'Origin')
        self.end_headers()
    def engine(self, path, data=None):
        req = urllib.request.Request('http://127.0.0.1:8765' + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=3) as r: return r.read()
    def do_GET(self):
        path = self.path.split('?')[0]
        files = {'/': ('index.html','text/html; charset=utf-8'), '/index.html': ('index.html','text/html; charset=utf-8'), '/app.js': ('app.js','text/javascript'), '/style.css': ('style.css','text/css')}
        if path in files:
            name, mime = files[path]
            return self.respond(200, (WEB/name).read_bytes(), mime)
        if not self.authorized(): return self.respond(401, {'error': 'Enter the pairing key shown by the bridge'})
        if path == '/api/status':
            result = {'engine': None, 'osc': 'OSC destination localhost:' + str(self.server.osc_port), 'xy': self.server.xy}
            try: result['engine'] = json.loads(self.engine('/status'))
            except (OSError, ValueError): result['engine_error'] = 'Start LiveGrid for image controls. XY still sends OSC.'
            return self.respond(200, result)
        if path == '/api/preview':
            try: return self.respond(200, self.engine('/preview.jpg'), 'image/jpeg')
            except OSError: return self.respond(503, {'error': 'Preview unavailable'})
        self.respond(404, {'error': 'Not found'})
    def do_POST(self):
        if not self.authorized(): return self.respond(401, {'error': 'Pairing key or origin rejected'})
        if self.path != '/api/control': return self.respond(404, {'error': 'Not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 8192 or not self.headers.get('Content-Type','').startswith('application/json'):
                raise ValueError('JSON required, maximum 8192 bytes')
            data = validate(json.loads(self.rfile.read(size)))
            engine_data = {k:v for k,v in data.items() if k not in ('x','y')}
            # Do not report success or emit mirrored OSC when the engine rejected a control.
            if engine_data: self.engine('/control', engine_data)
            for k,v in data.items():
                if k in ('x','y'): self.server.xy[k] = v
                if k == 'prompt': continue
                if k == 'layout': v = int(v == 'repeat')
                self.server.udp.sendto(osc('/livegrid/'+k, v), ('127.0.0.1', self.server.osc_port))
            self.respond(200, {'ok': True})
        except (ValueError, TypeError): self.respond(400, {'error': 'Invalid control values'})
        except OSError: self.respond(502, {'error': 'LiveGrid is unavailable; start the engine on port 8765'})

def make_server(host='127.0.0.1', port=8780, token=None, osc_port=9000, public_origin=None):
    server = ThreadingHTTPServer((host, port), Handler)
    server.token = token or secrets.token_urlsafe(24)
    server.osc_port = osc_port
    server.public_origin = public_origin
    server.xy = {'x': .5, 'y': .5}
    server.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return server

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--lan', action='store_true', help='Allow phones on the local network')
    p.add_argument('--port', type=int, default=8780)
    p.add_argument('--osc-port', type=int, default=9000)
    p.add_argument('--public-origin', help='Optional HTTPS tunnel origin (no trailing slash)')
    a = p.parse_args()
    server = make_server('0.0.0.0' if a.lan else '127.0.0.1', a.port, osc_port=a.osc_port, public_origin=a.public_origin)
    print('LiveGrid Mobile bridge — keep this window open', flush=True)
    print('Pairing key (private, changes on restart): ' + server.token, flush=True)
    print('Computer controller: http://127.0.0.1:' + str(a.port), flush=True)
    if a.lan:
        for ip in sorted(set(socket.gethostbyname_ex(socket.gethostname())[2])):
            if not ip.startswith('127.'): print('Possible phone address: http://' + ip + ':' + str(a.port), flush=True)
    print('OSC → localhost:' + str(a.osc_port) + ' | Ctrl+C stops this add-on', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close(); server.udp.close()
