import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import io, json, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import urllib.request
import urllib.error

from inference_pool import resolve_pool_backend, create_pool_proxy

class MockStore:
    def __init__(self):
        self.records = []
    def identity(self, account):
        return f"test-user-{account}"
    def record(self, account, model, in_tok, out_tok, status, duration, identity=None):
        self.records.append((account, model, in_tok, out_tok, status, identity))

class InferencePoolTests(unittest.TestCase):
    def test_resolve_pool_backend_priority(self):
        catalog_mock = {
            'selected': 'coder2',
            'profiles': {
                'rapido': {'account': 1, 'port': 18134, 'enabled': True},
                'coder2': {'account': 2, 'port': 17860, 'enabled': True}
            }
        }
        # If coder2 is healthy, it should be selected first
        k, p = resolve_pool_backend(catalog_mock, 'coder2', probe_fn=lambda port: port == 17860)
        self.assertEqual(k, 'coder2')
        self.assertEqual(p['account'], 2)

        # If coder2 is down but rapido is healthy, failover to rapido
        k, p = resolve_pool_backend(catalog_mock, 'coder2', probe_fn=lambda port: port == 18134)
        self.assertEqual(k, 'rapido')
        self.assertEqual(p['account'], 1)

        # If none is healthy
        k, p = resolve_pool_backend(catalog_mock, 'coder2', probe_fn=lambda port: False)
        self.assertIsNone(k)
        self.assertIsNone(p)

    def test_pool_status_endpoint(self):
        store = MockStore()
        catalog_mock = {
            'selected': 'coder2',
            'profiles': {
                'coder2': {'account': 2, 'port': 17860, 'model': 'qwen', 'enabled': True}
            }
        }
        server = create_pool_proxy(
            port=19001,
            store=store,
            catalog_fn=lambda: catalog_mock,
            wait_timeout=1
        )
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = urllib.request.Request('http://127.0.0.1:19001/api/pool/status')
            with urllib.request.urlopen(req, timeout=2) as r:
                data = json.loads(r.read().decode('utf-8'))
                self.assertEqual(data['pool_port'], 19001)
                self.assertIn('ready', data)
        finally:
            server.shutdown()
            server.server_close()

    def test_pool_public_auth_required(self):
        store = MockStore()
        catalog_mock = {'selected': 'coder2', 'profiles': {}}
        server = create_pool_proxy(
            port=19002,
            store=store,
            catalog_fn=lambda: catalog_mock,
            wait_timeout=1
        )
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = urllib.request.Request(
                'http://127.0.0.1:19002/v1/models',
                headers={'X-IA-Public': '1'}
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=2)
            self.assertEqual(ctx.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()

    def test_pool_unavailable_returns_503(self):
        store = MockStore()
        catalog_mock = {
            'selected': 'coder2',
            'profiles': {
                'coder2': {'account': 2, 'port': 17869, 'enabled': True}
            }
        }
        # Backend port 17869 is closed -> should return 503
        server = create_pool_proxy(
            port=19003,
            store=store,
            catalog_fn=lambda: catalog_mock,
            wait_timeout=1
        )
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = urllib.request.Request(
                'http://127.0.0.1:19003/v1/chat/completions',
                data=b'{"model":"qwen","messages":[]}',
                headers={'Content-Type': 'application/json'}
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=3)
            self.assertEqual(ctx.exception.code, 503)
            body = json.loads(ctx.exception.read().decode('utf-8'))
            self.assertEqual(body['error']['type'], 'backend_unavailable')
        finally:
            server.shutdown()
            server.server_close()


from pool_orchestrator import evaluate_candidate_accounts, rank_pool_accounts, should_prewarm_next

class PoolOrchestratorTests(unittest.TestCase):
    def test_prewarm_triggers_8_minutes_before_max_session(self):
        # At 110 min of a 120 min session (6600s >= 7200 - 480 = 6720? No, 6600 < 6720)
        prewarm, reason = should_prewarm_next(session_elapsed_seconds=6600, max_session_minutes=120)
        self.assertFalse(prewarm)

        # At 113 min (6780s >= 6720) -> should prewarm!
        prewarm, reason = should_prewarm_next(session_elapsed_seconds=6780, max_session_minutes=120)
        self.assertTrue(prewarm)
        self.assertEqual(reason, 'session_limit_approaching')

    def test_prewarm_triggers_on_low_quota(self):
        prewarm, reason = should_prewarm_next(session_elapsed_seconds=100, quota_remaining_seconds=300)
        self.assertTrue(prewarm)
        self.assertEqual(reason, 'quota_exhaustion_approaching')

    def test_rank_pool_accounts_prefers_highest_quota(self):
        profiles = {
            'c1': {'account': 1, 'enabled': True},
            'c2': {'account': 2, 'enabled': True},
            'c3': {'account': 3, 'enabled': True}
        }
        quota_data = {
            '1': {'available_seconds': 5000},
            '2': {'available_seconds': 25000},
            '3': {'available_seconds': 15000}
        }
        ranked = rank_pool_accounts(['c1', 'c2', 'c3'], profiles, quota_data=quota_data)
        self.assertEqual(ranked, ['c2', 'c3', 'c1'])

if __name__ == '__main__':
    unittest.main()
