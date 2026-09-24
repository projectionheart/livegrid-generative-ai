import json
import socket
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
from bridge import make_server, osc, validate, Handler

class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cls.udp.bind(('127.0.0.1',0)); cls.udp.settimeout(1)
        cls.server = make_server(port=0, token='test-only-key', osc_port=cls.udp.getsockname()[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.server.udp.close(); cls.udp.close()
    def request(self,path,data=None,key='test-only-key',origin='https://projectionheart.github.io'):
        req=urllib.request.Request(self.base+path, data=json.dumps(data).encode() if data is not None else None,
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Origin':origin})
        return urllib.request.urlopen(req,timeout=2)
    def test_auth_and_origin(self):
        for key,origin in [('bad','https://projectionheart.github.io'),('test-only-key','https://example.com')]:
            with self.assertRaises(urllib.error.HTTPError) as c: self.request('/api/status',key=key,origin=origin)
            self.assertEqual(c.exception.code,401)
    def test_xy_osc_without_engine(self):
        with self.request('/api/control',{'x':.25,'y':.75}) as r: self.assertEqual(r.status,200)
        self.assertEqual(self.udp.recv(1024),osc('/livegrid/x',.25))
        self.assertEqual(self.udp.recv(1024),osc('/livegrid/y',.75))
    def test_engine_forwarding(self):
        with patch.object(Handler,'engine',return_value=b'{"ok":true}') as engine:
            with self.request('/api/control',{'brightness':.4}) as r: self.assertEqual(r.status,200)
            engine.assert_called_once_with('/control',{'brightness':.4})
            self.assertEqual(self.udp.recv(1024),osc('/livegrid/brightness',.4))
    def test_failed_engine_does_not_claim_success(self):
        with patch.object(Handler,'engine',side_effect=OSError()):
            with self.assertRaises(urllib.error.HTTPError) as c: self.request('/api/control',{'blackout':True})
            self.assertEqual(c.exception.code,502)
    def test_validation(self):
        for data in [{'x':float('nan')},{'brightness':2},{'freeze':'yes'},{'prompt':''},{'whatever':1},[]]:
            with self.assertRaises(ValueError):validate(data)
    def test_static_and_status(self):
        with urllib.request.urlopen(self.base+'/') as r:self.assertIn(b'LiveGrid Mobile',r.read())
        with patch.object(Handler,'engine',side_effect=OSError()):
            with self.request('/api/status') as r:
                self.assertEqual(r.headers['Access-Control-Allow-Origin'],'https://projectionheart.github.io')
                self.assertIsNone(json.load(r)['engine'])

if __name__=='__main__': unittest.main()
