import base64,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from panel_auth import PasswordGate,password_record
from panel_security import panel_host,mutation_allowed

class AuthenticationTests(unittest.TestCase):
    def test_password_is_hashed_and_invalid_credentials_are_rejected(self):
        password='example-only-long-password'
        record=password_record('admin',password)
        self.assertNotIn(password,json.dumps(record))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'auth.json';path.write_text(json.dumps(record));gate=PasswordGate(path)
            header=lambda p:'Basic '+base64.b64encode(('admin:'+p).encode()).decode()
            self.assertTrue(gate.verify(header(password)))
            self.assertFalse(gate.verify(header('wrong')))
            self.assertFalse(gate.verify('Bearer nope'))
            gate.failures['attacker']=[__import__('time').monotonic()]*20
            self.assertFalse(gate.verify(header(password),'attacker'))
            self.assertTrue(gate.verify(header(password),'owner'))
    def test_public_origin_is_explicit_and_csrf_still_required(self):
        with patch.dict('os.environ',{'IA_PUBLIC_ORIGIN':'https://ia.example.test'}):
            self.assertTrue(panel_host('ia.example.test',8765))
            headers={'Host':'ia.example.test','Origin':'https://ia.example.test','X-IA-Token':'test'}
            self.assertTrue(mutation_allowed(headers,'test',8765))
            self.assertFalse(mutation_allowed({**headers,'Origin':'https://other.test'},'test',8765))
            self.assertFalse(mutation_allowed({**headers,'X-IA-Token':''},'test',8765))
