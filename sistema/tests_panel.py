import unittest,tempfile,threading,time
from pathlib import Path
from unittest.mock import patch
from panel_server import Dashboard
from panel_security import mutation_allowed
class PanelPolicyTests(unittest.TestCase):
    def test_only_local_host_and_session_header_can_mutate(self):
        base={'Host':'127.0.0.1:8765','Origin':'http://127.0.0.1:8765','X-IA-Token':'sample'}
        self.assertTrue(mutation_allowed(base,'sample',8765))
        for changed in [{'Origin':'https://other.example'},{'Host':'other.example:8765'},{'X-IA-Token':'wrong'}]:
            self.assertFalse(mutation_allowed({**base,**changed},'sample',8765))
        self.assertFalse(mutation_allowed({'Host':'127.0.0.1:8765'},'sample',8765))
if __name__=='__main__':unittest.main()

class StopPriorityTests(unittest.TestCase):
    def test_stop_is_queued_and_cancels_start_while_operation_busy(self):
        with tempfile.TemporaryDirectory() as tmp,patch('panel_server.UsageStore'),patch('panel_server.ChatStore'):
            app=Dashboard();app.cancel_file=Path(tmp)/'cancel';app.operation.acquire()
            called=threading.Event()
            def stopped(data):
                self.assertEqual(data['action'],'stop_all');app.operation.release();called.set()
            app.run=stopped
            app.begin({'action':'stop_all'})
            self.assertTrue(app.cancel_file.exists());self.assertFalse(called.is_set())
            app.operation.release();self.assertTrue(called.wait(2))

class PendingStopTests(unittest.TestCase):
    def test_new_action_cannot_overtake_accepted_stop(self):
        with tempfile.TemporaryDirectory() as tmp,patch('panel_server.UsageStore'),patch('panel_server.ChatStore'):
            app=Dashboard();app.cancel_file=Path(tmp)/'cancel';app.stop_pending=True;app.run=lambda _: app.operation.release()
            with self.assertRaises(ValueError):app.begin({'action':'start','key':'rapido'})
            self.assertTrue(app.operation.acquire(blocking=False));app.operation.release()
