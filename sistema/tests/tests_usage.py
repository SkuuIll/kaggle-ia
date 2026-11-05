import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from datetime import timedelta,datetime
from usage import UsageStore,UsageParser,quota_values
class UsageTests(unittest.TestCase):
    def test_sse_fragmented_usage_counts_once(self):
        parser=UsageParser()
        for part in [b'data: {"usage":{"prompt_',b'tokens":12,"completion_tokens":5}}\n\n',b'data: [DONE]\n\n']:parser.feed(part)
        self.assertEqual(parser.finish(),(12,5))
    def test_missing_usage_is_unknown_not_zero(self):
        parser=UsageParser();parser.feed(b'data: {"choices":[]}\n\n')
        self.assertIsNone(parser.finish())
    def test_native_ndjson_and_responses_usage(self):
        parser=UsageParser();parser.feed(b'{"response":"hello","done":false}\n{"prompt_eval_count":9,"eval_count":2}\n')
        self.assertEqual(parser.finish(),(9,2))
        parser=UsageParser();parser.feed(b'data: {"response":{"usage":{"input_tokens":8,"output_tokens":3}}}\n\n')
        self.assertEqual(parser.finish(),(8,3))
    def test_store_keeps_counters_without_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=UsageStore(Path(tmp)/'usage.sqlite');store.record(2,'model',12,5,200,1.0)
            self.assertEqual(store.totals(2)['output_tokens'],5)
            self.assertEqual(store.totals(1)['requests'],0)
    def test_official_quota_includes_reserved_time(self):
        q=SimpleNamespace(gpu_quota=SimpleNamespace(time_used=timedelta(hours=2),time_reserved=timedelta(hours=1),total_time_allowed=timedelta(hours=30)),quota_refresh_time=datetime(2026,11,7))
        d=quota_values(q);self.assertEqual(d['available_seconds'],27*3600)
        q.gpu_quota.total_time_allowed=None;self.assertIsNone(quota_values(q)['available_seconds'])
if __name__=='__main__':unittest.main()
