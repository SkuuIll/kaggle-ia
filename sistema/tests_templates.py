import copy,json,tempfile,unittest,zipfile
from pathlib import Path
from templates import MODELS,prepare_profile,get_template
from tool_templates import build_tool_package

class TemplateTests(unittest.TestCase):
 def metadata(self,t):return {'sha':t['revision'],'siblings':[{'rfilename':t['filename'],'size':t['size_bytes']}],'gguf':{'context_length':t['native_context']}}
 def test_template_preserves_account_relay_and_alias(self):
  t=MODELS[0];original={'account':2,'port':17860,'model':'fixed-alias','kernel_ref':'owner/private','label':'Old'}
  result=prepare_profile(original,t['id'],self.metadata(t))
  for key in ('account','port','model','kernel_ref'):self.assertEqual(result[key],original[key])
  self.assertEqual(original['label'],'Old');self.assertEqual(result['revision'],t['revision'])
 def test_changed_revision_or_missing_file_is_rejected(self):
  t=MODELS[0];d=self.metadata(t);d['sha']='0'*40
  with self.assertRaises(ValueError):prepare_profile({'account':1},t['id'],d)
  d=self.metadata(t);d['siblings']=[]
  with self.assertRaises(ValueError):prepare_profile({'account':1},t['id'],d)
 def test_unknown_template_never_becomes_a_shell_command(self):
  with self.assertRaises(ValueError):get_template('https://example.test/install.sh')
 def test_budget_fits_reported_native_context(self):
  self.assertEqual(len(MODELS),1)
  for t in MODELS:self.assertLessEqual(t['context'],t['native_context']);self.assertLess(t['size_bytes'],24*1024**3)
 def test_private_tool_package_does_not_put_key_in_scripts(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'tool.zip';build_tool_package('httpx',{'model':'alias','context':32768},{'url':'https://ia.example.test/v1','token':'private-test-key'},path)
   with zipfile.ZipFile(path) as z:
    self.assertEqual(json.loads(z.read('connection.json'))['token'],'private-test-key')
    self.assertNotIn('private-test-key',z.read('INSTALAR.bat').decode())
    self.assertNotIn('private-test-key',z.read('install_tool.py').decode())
    self.assertFalse(any('kaggle(' in n or n.endswith('.ipynb') for n in z.namelist()))
    for name in ['install_tool.py','launch.py','client.py']:compile(z.read(name),name,'exec')

 def test_install_refuses_unconfirmed_state_without_mutating_config(self):
  from panel_server import Dashboard
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as folder,patch('panel_server.UsageStore'),patch('panel_server.ChatStore'),patch('coding_control.probe_state',return_value='UNKNOWN'),patch('panel_server.save_catalog') as save:
   app=Dashboard();app.cancel_file=Path(folder)/'cancel'
   with self.assertRaises(ValueError):app.install_template('coder2','qwen38-heretic-rvn')
   save.assert_not_called()
 def test_prepare_template_builds_notebook_without_gpu_start(self):
  from panel_server import Dashboard
  from unittest.mock import patch,Mock
  profile={'account':2,'port':17860,'model':'alias','label':'Old'}
  with tempfile.TemporaryDirectory() as folder,patch('panel_server.UsageStore'),patch('panel_server.ChatStore'),patch('coding_control.probe_state',return_value='COMPLETE'),patch('panel_server.catalog',return_value={'profiles':{'coder2':profile}}),patch('panel_server.save_catalog') as save,patch('panel_server.requests.get') as get,patch('panel_server.subprocess.run',return_value=Mock(returncode=0)) as run:
   get.return_value.json.return_value=self.metadata(get_template('qwen38-heretic-rvn'));app=Dashboard();app.cancel_file=Path(folder)/'cancel';app.control=Mock()
   app.install_template('coder2','qwen38-heretic-rvn');app.control.assert_not_called()
   self.assertEqual(save.call_args.args[0]['profiles']['coder2']['template_id'],'qwen38-heretic-rvn')
   self.assertIn('build_single_notebook.py',str(run.call_args.args[0]));self.assertNotIn('start',run.call_args.args[0])

 def test_all_curated_models_are_low_restriction_variants(self):
  for model in MODELS:
   self.assertTrue(model['low_restriction'])
   self.assertTrue('abliterated' in model['repo'].lower() or model['id']=='cybertiel')
