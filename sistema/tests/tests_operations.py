import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import unittest
from operations import limits,diagnostic,PROFILES
class OperationsTests(unittest.TestCase):
 def test_busy_generation_has_no_idle_deadline(self):self.assertIsNone(limits(0,0,1,100,5,120)['idle_remaining'])
 def test_limits_never_negative(self):self.assertEqual(limits(0,0,0,9999,5,120)['session_remaining'],0)
 def test_diagnosis_distinguishes_failure_layers(self):
  self.assertIn('apagada',diagnostic('COMPLETE',503,False));self.assertIn('clave',diagnostic('RUNNING',401,False));self.assertIn('daemon',diagnostic('RUNNING',200,True))
 def test_profiles_do_not_exceed_current_native_configuration(self):self.assertTrue(all(4096<=p['context']<=131072 for p in PROFILES.values()))

 def test_error_history_does_not_persist_exception_secrets(self):
  from operations import failure_detail
  self.assertNotIn('secret',failure_detail(ConnectionError('secret')))
 def test_history_migration_retains_old_records_and_new_reasons(self):
  import sqlite3,tempfile
  from pathlib import Path
  from usage import UsageStore
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'usage.sqlite'
   with sqlite3.connect(path) as db:
    db.execute('CREATE TABLE events(id INTEGER PRIMARY KEY,timestamp REAL,action TEXT,profile TEXT,status TEXT)')
    db.execute("INSERT INTO events VALUES(1,1,'stop','coder2','done')")
   db.close()
   store=UsageStore(path);store.event('start','coder2','error','No hay conexión')
   rows=UsageStore(path).events()
   self.assertEqual(rows[0]['detail'],'No hay conexión');self.assertEqual(rows[1]['detail'],'')
 def test_selected_output_budget_reaches_client_configuration(self):
  import json
  from client_configs import build_configs
  p={'account':2,'provider_id':'test','paseo_provider':'test','model':'test','label':'Test','context':16384,'output_tokens':1024,'temperature':0.2}
  snippets=build_configs(p,{'url':'https://example.test/v1','token':'dummy'})
  model=json.loads(snippets['opencode'])['provider']['test']['models']['test']
  self.assertEqual(model['limit'],{'context':16384,'output':1024})

 def test_preset_label_matches_its_context_without_starting_gpu(self):
  from operations import apply_profile
  p={'label':'Coder - 128k (cuenta 2)'};apply_profile(p,'codigo')
  self.assertEqual(p['context'],32768);self.assertEqual(p['output_tokens'],4096)
  self.assertEqual(p['label'],'Coder - 32k (cuenta 2)')
