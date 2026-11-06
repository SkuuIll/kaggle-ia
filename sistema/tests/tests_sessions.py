import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

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
        guest=s.create('guest')
        s.revoke_user('admin');self.assertIsNone(s.get(one));self.assertIsNone(s.get(two))
        self.assertIsNotNone(s.get(guest))
    def test_password_change_requires_current_password(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'auth.json';path.write_text(json.dumps(password_record('admin','old-password-example-123')))
            gate=PasswordGate(path)
            self.assertFalse(gate.change_password('admin','wrong','new-password-example-456'))
            self.assertTrue(gate.change_password('admin','old-password-example-123','new-password-example-456'))
            self.assertTrue(gate.check('admin','new-password-example-456'))
            self.assertFalse(gate.check('admin','old-password-example-123'))
    def test_invited_users_persist_and_cannot_overwrite_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'auth.json'
            owner='owner-password-example'
            guest='guest-password-example'
            path.write_text(json.dumps(password_record('admin',owner)))
            gate=PasswordGate(path)
            with self.assertRaises(ValueError):gate.create_user('admin',guest)
            with self.assertRaises(ValueError):gate.create_user('../guest',guest)
            gate.create_user('guest',guest)
            with self.assertRaises(ValueError):gate.create_user('guest',owner)
            gate=PasswordGate(path)
            self.assertEqual(gate.list_users(),['guest'])
            self.assertEqual(gate.role('guest'),'observer')
            self.assertTrue(gate.check('guest',guest))
            self.assertTrue(gate.change_password('guest',guest,owner))
            self.assertTrue(gate.check('admin',owner))
            gate.remove_user('guest')
            self.assertFalse(PasswordGate(path).check('guest',owner))
