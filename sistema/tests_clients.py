import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import model_profiles
class ClientSetupTests(unittest.TestCase):
    def test_one_account_removes_disabled_slot_from_client_lists(self):
        data=model_profiles.catalog();data['profiles']['coder2']['enabled']=False;data['selected']='rapido'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'program/sistema';base.mkdir(parents=True)
            file=base/'model_profiles.json';file.write_text(json.dumps(data))
            with patch.object(Path,'home',return_value=root),patch.object(model_profiles,'BASE',base),patch.object(model_profiles,'CATALOG',file):model_profiles.sync_clients('rapido')
            config=json.loads((root/'.config/opencode/opencode.json').read_text())
            self.assertNotIn('kaggle2',config['provider'])
            paseo=json.loads((root/'.paseo/config.json').read_text())
            self.assertEqual(len(paseo['agents']['providers']['qwen-kaggle']['models']),1)
    def test_fresh_install_lists_both_accounts_in_one_paseo_picker(self):
        data=model_profiles.catalog()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'program/sistema';base.mkdir(parents=True)
            catalog=base/'model_profiles.json';catalog.write_text(json.dumps(data))
            with patch.object(Path,'home',return_value=root),patch.object(model_profiles,'BASE',base),patch.object(model_profiles,'CATALOG',catalog):
                model_profiles.sync_clients('coder2')
            paseo=json.loads((root/'.paseo/config.json').read_text(encoding='utf8'))
            models=paseo['agents']['providers']['qwen-kaggle']['models']
            self.assertEqual({m['id'] for m in models},{'kaggle/cybertiel-coder','kaggle2/qwen38-coder390'})
            self.assertEqual([m['id'] for m in models if m.get('isDefault')],['kaggle2/qwen38-coder390'])
            self.assertEqual({m['id'] for m in paseo['agents']['providers']['qwen-coder390']['models']},{'kaggle/cybertiel-coder','kaggle2/qwen38-coder390'})
            config=json.loads((root/'.config/opencode/opencode.json').read_text())
            self.assertEqual(config['provider']['kaggle2']['options']['baseURL'],'http://127.0.0.1:19860/v1')
            self.assertEqual(paseo['daemon']['listen'],'127.0.0.1:6767')
    def test_https_clients_use_scoped_key_instead_of_loopback(self):
        data=model_profiles.catalog()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'program/sistema';(base/'.private').mkdir(parents=True)
            file=base/'model_profiles.json';file.write_text(json.dumps(data))
            (base/'.private/api-clients.json').write_text(json.dumps({str(n):{'url':f'https://ia.example.test/inference/cuenta{n}/v1','token':f'example-token-{n}'} for n in (1,2)}))
            with patch.object(Path,'home',return_value=root),patch.object(model_profiles,'BASE',base),patch.object(model_profiles,'CATALOG',file):model_profiles.sync_clients('coder2')
            config=json.loads((root/'.config/opencode/opencode.json').read_text())
            self.assertEqual(config['provider']['kaggle2']['options']['baseURL'],'https://ia.example.test/inference/cuenta2/v1')
            self.assertEqual(config['provider']['kaggle2']['options']['apiKey'],'example-token-2')
    def test_only_account_two_can_be_configured_without_account_one(self):
        data=model_profiles.catalog();data['profiles']['rapido']['enabled']=False
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'program/sistema';base.mkdir(parents=True)
            file=base/'model_profiles.json';file.write_text(json.dumps(data))
            with patch.object(Path,'home',return_value=root),patch.object(model_profiles,'BASE',base),patch.object(model_profiles,'CATALOG',file):model_profiles.sync_clients('coder2')
            config=json.loads((root/'.paseo/config.json').read_text())
            self.assertEqual([m['id'] for m in config['agents']['providers']['qwen-kaggle']['models']],['kaggle2/qwen38-coder390'])
if __name__=='__main__':unittest.main()
