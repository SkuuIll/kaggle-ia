import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from cpu_cache import prepare,expected_artifact,validate_manifest,source_for,CACHE_READER,status,launch

class CPUCacheTests(unittest.TestCase):
 def profile(self):return {'account':2,'kernel_ref':'owner/coder','repo':'author/model','revision':'a'*40,'filename':'weights.gguf'}
 def expected(self):return {'repo':'author/model','revision':'a'*40,'filename':'weights.gguf','size_bytes':4,'sha256':hashlib.sha256(b'data').hexdigest(),'schema':1}
 def test_cpu_recipe_has_no_accelerator_or_credentials_and_is_private(self):
  with tempfile.TemporaryDirectory() as folder,patch('cpu_cache.expected_artifact',return_value=self.expected()):
   info,path=prepare(self.profile(),'coder2',folder)
   metadata=json.loads((path/'kernel-metadata.json').read_text());code=(path/'cache_cpu.py').read_text()
   self.assertEqual(metadata['enable_gpu'],'false');self.assertEqual(metadata['enable_tpu'],'false');self.assertEqual(metadata['is_private'],'true')
   self.assertNotIn('api_token',code);self.assertNotIn('kaggle_relay',code);self.assertNotIn('PRIVATE KEY',code)
   compile(code,'cache','exec');self.assertTrue(info['kernel_ref'].startswith('owner/ia-weights-cache-'))
 def test_manifest_cannot_attach_other_revision(self):
  bad=self.expected()|{'revision':'b'*40}
  with self.assertRaises(ValueError):validate_manifest(bad,self.expected())
 def test_profile_change_disables_stale_cache_and_other_owner_is_refused(self):
  p=self.profile();p['cache_source']=self.expected()|{'kernel_ref':'owner/ia-weights-cache-123456abcdef'}
  self.assertIsNotNone(source_for(p));p['revision']='b'*40;self.assertIsNone(source_for(p))
  p['cache_source']['kernel_ref']='other/ia-weights-cache-123456abcdef'
  with self.assertRaises(ValueError):source_for(p)
 def test_unverified_hash_or_oversized_file_cannot_be_prepared(self):
  for size,sha in [(4,None),(20*1024**3,'a'*64)]:
   response=Mock();response.json.return_value={'sha':'a'*40,'siblings':[{'rfilename':'weights.gguf','size':size,'lfs':{'sha256':sha}}]}
   with patch('cpu_cache.requests.get',return_value=response):
    with self.assertRaises(ValueError):expected_artifact(self.profile())
 def test_launch_does_not_publish_again_when_same_cache_complete(self):
  with tempfile.TemporaryDirectory() as folder,patch('cpu_cache.expected_artifact',return_value=self.expected()),patch('coding_control.state',return_value='COMPLETE'):
   client=Mock();result=launch(self.profile(),'coder2',folder,client)
   self.assertFalse(result['started']);client.kernels_push.assert_not_called()
 def test_missing_fresh_manifest_cannot_reuse_old_manifest(self):
  with tempfile.TemporaryDirectory() as folder,patch('cpu_cache.expected_artifact',return_value=self.expected()):
   info,path=prepare(self.profile(),'coder2',folder);manifest=path/'manifest/manifest.json';manifest.parent.mkdir();manifest.write_text(json.dumps(self.expected()))
   client=Mock();client.kernels_status.return_value.status='COMPLETE'
   with self.assertRaises(ValueError):status(self.profile(),'coder2',folder,client,attach=True)
 def test_gpu_reader_fails_closed_if_configured_cache_is_missing(self):
  ns={};exec(CACHE_READER,ns)
  with patch.object(ns['Path'],'glob',return_value=iter([])):
   with self.assertRaises(RuntimeError):ns['find_cached_weights']({'cache_source':self.expected()})
  self.assertIsNone(ns['find_cached_weights']({}))

 def test_reader_checks_file_contents_not_only_length(self):
  with tempfile.TemporaryDirectory() as folder:
   manifest=Path(folder)/'manifest.json';manifest.write_text(json.dumps(self.expected()));(Path(folder)/'weights.gguf').write_bytes(b'data')
   ns={};exec(CACHE_READER,ns)
   with patch.object(ns['Path'],'glob',return_value=iter([manifest])):
    self.assertEqual(ns['find_cached_weights']({'cache_source':self.expected()}),str((Path(folder)/'weights.gguf').resolve()))
   (Path(folder)/'weights.gguf').write_bytes(b'evil')
   with patch.object(ns['Path'],'glob',return_value=iter([manifest])):
    with self.assertRaises(RuntimeError):ns['find_cached_weights']({'cache_source':self.expected()})
 def test_cache_attach_downloads_only_fresh_manifest_and_sets_pinned_source(self):
  with tempfile.TemporaryDirectory() as folder,patch('cpu_cache.expected_artifact',return_value=self.expected()):
   info,path=prepare(self.profile(),'coder2',folder)
   client=Mock();client.kernels_status.return_value.status='COMPLETE'
   def output(*args,**kwargs):
    self.assertEqual(kwargs['file_pattern'],r'^manifest\.json$');(Path(kwargs['path'])/'manifest.json').write_text(json.dumps(self.expected()))
   client.kernels_output.side_effect=output;profile=self.profile()
   result=status(profile,'coder2',folder,client,attach=True)
   self.assertTrue(result['verified']);self.assertTrue(result['attached']);self.assertEqual(profile['cache_source']['kernel_ref'],info['kernel_ref'])
