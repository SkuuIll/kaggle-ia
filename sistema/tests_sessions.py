import unittest,tempfile,json
from pathlib import Path
from panel_auth import Sessions,PasswordGate,password_record
class SessionTests(unittest.TestCase):
    def test_expiry_and_logout_revoke_server_session(self):
        clock=[100.0];sessions=Sessions(clock=lambda:clock[0]);token=sessions.create('admin')
        self.assertEqual(sessions.get(token)['username'],'admin')
        self.assertIsNone(sessions.get('invented'))
        sessions.revoke(token);self.assertIsNone(sessions.get(token))
        other=sessions.create('admin');clock[0]+=28801;self.assertIsNone(sessions.get(other))
    def test_each_login_gets_new_csrf_and_password_change_revokes_sessions(self):
        s=Sessions();one=s.create('admin');two=s.create('admin')
        self.assertNotEqual(s.get(one)['csrf'],s.get(two)['csrf'])
        s.clear();self.assertIsNone(s.get(one));self.assertIsNone(s.get(two))
    def test_password_change_requires_current_password(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'auth.json';path.write_text(json.dumps(password_record('admin','old-password-example-123')))
            gate=PasswordGate(path)
            self.assertFalse(gate.change_password('wrong','new-password-example-456'))
            self.assertTrue(gate.change_password('old-password-example-123','new-password-example-456'))
            self.assertTrue(gate.check('admin','new-password-example-456'))
            self.assertFalse(gate.check('admin','old-password-example-123'))
