import unittest,json
from client_configs import build_configs,CLIENT_LAUNCHERS
class ClientConfigTests(unittest.TestCase):
 def test_configs_use_exact_https_key_alias_and_context(self):
  p={'account':2,'provider_id':'kaggle2','paseo_provider':'qwen-coder390','model':'coder','label':'Coder','context':131072,'temperature':0.2,'effort':'none','reasoning':True}
  result=build_configs(p,{'url':'https://ia.example.test/inference/cuenta2/v1','token':'test-private-key'})
  options=json.loads(result['opencode'])['provider']['kaggle2']['options']
  self.assertEqual(options['baseURL'],'https://ia.example.test/inference/cuenta2/v1');self.assertEqual(options['apiKey'],'test-private-key')
  self.assertIn('test-private-key',result['continue']);self.assertIn('131072',result['continue'])
  self.assertEqual(json.loads(result['opencode'])['model'],'kaggle2/coder')
  self.assertNotIn('test-private-key',result['paseo'])
  self.assertEqual(json.loads(result['paseo'])['agents']['providers']['qwen-coder390']['models'][0]['id'],'kaggle2/coder')
 def test_client_launchers_are_bundled_in_memory_without_secrets(self):
  self.assertEqual(set(CLIENT_LAUNCHERS),{'INSTALAR.bat','CONFIGURAR_CLIENTES.bat','ABRIR_PASEO.bat','sistema/python_ia.bat'})
  for content in CLIENT_LAUNCHERS.values():
   self.assertNotIn('KGAT_',content)
   self.assertNotIn('PRIVATE KEY',content)
