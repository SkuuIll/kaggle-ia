import unittest,tempfile,json,hashlib
from pathlib import Path
from inference_auth import allowed
class ScopedBearerTests(unittest.TestCase):
 def test_missing_wrong_and_other_account_tokens_cannot_access(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'auth.json';p.write_text(json.dumps({'1':hashlib.sha256(b'token-one').hexdigest(),'2':hashlib.sha256(b'token-two').hexdigest()}))
   self.assertTrue(allowed('Bearer token-one',1,p))
   self.assertFalse(allowed('Bearer token-one',2,p))
   self.assertFalse(allowed('Bearer wrong',1,p))
   self.assertFalse(allowed('',1,p))
   self.assertFalse(allowed('Bearer token-one',1,Path(folder)/'missing'))
