import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from panel_server import Dashboard
class AccountTests(unittest.TestCase):
    def test_kgat_detects_username_without_manual_entry(self):
        with tempfile.TemporaryDirectory() as folder,patch('panel_server.UsageStore'):
            base=Path(folder);(base/'.private').mkdir()
            config={'selected':'rapido','profiles':{'rapido':{'account':1,'kernel_ref':'placeholder/test'}}}
            app=Dashboard()
            with patch('panel_server.BASE',base),patch('panel_server.catalog',return_value=config),patch('panel_server.save_catalog') as saved,patch('panel_server.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'username':'detected_user'}))):
                app.credentials(None,{'key_value':'KGAT_'+'x'*30})
                credentials=json.loads((base/'kaggle(1).json').read_text())
                self.assertEqual(credentials['username'],'detected_user')
                self.assertEqual(saved.call_args.args[0]['profiles']['rapido']['kernel_ref'],'detected_user/test')
    def test_failed_validation_does_not_replace_credentials(self):
        with tempfile.TemporaryDirectory() as folder,patch('panel_server.UsageStore'):
            base=Path(folder);original=base/'kaggle(1).json';original.write_text('{"username":"old","key":"preserve"}')
            app=Dashboard()
            with patch('panel_server.BASE',base),patch('panel_server.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')):
                with self.assertRaises(ValueError):app.credentials('rapido',{'key_value':'KGAT_'+'x'*30})
            self.assertEqual(json.loads(original.read_text())['key'],'preserve')
