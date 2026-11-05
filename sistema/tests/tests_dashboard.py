import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import unittest,tempfile,json
from pathlib import Path
from usage import UsageStore
from account_management import remove_account
class DashboardDataTests(unittest.TestCase):
 def test_daily_series_is_real_isolated_and_empty_when_no_usage(self):
  with tempfile.TemporaryDirectory() as folder:
   store=UsageStore(Path(folder)/'usage.sqlite')
   self.assertEqual(store.daily(1),[])
   store.record(1,'test',20,8,200,2);store.record(2,'other',100,40,200,4)
   rows=store.daily(1)
   self.assertEqual(sum(r['output_tokens'] for r in rows),8)
   self.assertEqual(sum(r['requests'] for r in rows),1)
 def test_operation_history_survives_reopening_database(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'usage.sqlite';store=UsageStore(path)
   store.event('stop','rapido','done')
   self.assertEqual(UsageStore(path).events()[0]['action'],'stop')
 def test_remove_refuses_unknown_or_running_and_preserves_credential(self):
  with tempfile.TemporaryDirectory() as folder:
   base=Path(folder);path=base/'kaggle(1).json';path.write_text('{"username":"sample","key":"dummy"}')
   config={'selected':'rapido','profiles':{'rapido':{'account':1}}}
   for state in ('UNKNOWN','RUNNING','QUEUED'):
    with self.assertRaises(ValueError):remove_account(config,'rapido',base,lambda _:state)
    self.assertTrue(path.exists())
 def test_remove_archives_only_after_confirmed_stop(self):
  with tempfile.TemporaryDirectory() as folder:
   base=Path(folder);path=base/'kaggle(1).json';path.write_text('{"username":"sample","key":"dummy"}')
   config={'selected':'rapido','profiles':{'rapido':{'account':1}}}
   remove_account(config,'rapido',base,lambda _:'COMPLETE')
   self.assertFalse(path.exists());self.assertFalse(config['profiles']['rapido']['enabled'])
   self.assertEqual(len(list((base/'.private/removed-accounts').glob('*.json'))),1)

 def test_replacing_connection_keeps_metrics_separate_by_identity(self):
  with tempfile.TemporaryDirectory() as folder:
   store=UsageStore(Path(folder)/'usage.sqlite')
   store.bind_identity(1,'first_user');store.record(1,'model',20,8,200,2)
   store.bind_identity(1,'second_user');store.record(1,'model',5,2,200,1)
   self.assertEqual(store.totals(1,'second_user')['output_tokens'],2)
   self.assertEqual(store.totals(1,'first_user')['output_tokens'],8)
   self.assertEqual(sum(r['output_tokens'] for r in store.daily(1,'second_user')),2)
