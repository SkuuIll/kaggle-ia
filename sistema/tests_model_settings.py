import copy,json,tempfile,unittest
from pathlib import Path
from model_settings import parse_repo,update_model
class SettingsTests(unittest.TestCase):
    def test_repo_accepts_hf_and_rejects_credentials_or_other_sites(self):
        self.assertEqual(parse_repo('https://huggingface.co/author/model/tree/main'),'author/model')
        self.assertEqual(parse_repo('author/model'),'author/model')
        for value in ['https://example.org/author/model','https://huggingface.co/a/b?token=secret','../repo']:
            with self.assertRaises(ValueError):parse_repo(value)
    def test_change_requires_stop_and_preserves_routing_and_other_account(self):
        data={'selected':'a','profiles':{'a':{'model':'stable-alias','account':2,'port':17860,'repo':'old/model','kernel_ref':'owner/stable'},'b':{'model':'other'}}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'profiles.json';p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):update_model(p,'a','author/model','model.gguf','a'*40,131072,False)
            self.assertEqual(json.loads(p.read_text()),data)
            update_model(p,'a','author/model','model.gguf','a'*40,131072,True)
            result=json.loads(p.read_text());self.assertEqual(result['profiles']['b'],data['profiles']['b'])
            self.assertEqual(result['profiles']['a']['model'],'stable-alias');self.assertEqual(result['profiles']['a']['port'],17860)
if __name__=='__main__':unittest.main()
