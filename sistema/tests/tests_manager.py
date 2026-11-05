import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import unittest
from unittest.mock import patch,call
import ia_manager
from coding_control import require_no_other_active
class ManagerTests(unittest.TestCase):
    @patch.object(ia_manager,'catalog',return_value={'profiles':{'one':{},'two':{}}})
    @patch.object(ia_manager,'control',side_effect=[False,True])
    def test_stop_all_attempts_both_and_does_not_claim_success_on_partial_failure(self,control,catalog):
        self.assertFalse(ia_manager.stop_all())
        self.assertEqual(control.call_args_list,[call('stop','one'),call('stop','two')])
    def test_new_allocation_refuses_another_active_account(self):
        profiles={'a':{},'b':{}}
        with self.assertRaisesRegex(RuntimeError,'b'):
            require_no_other_active('a',profiles,lambda key:'RUNNING')
        require_no_other_active('a',profiles,lambda key:'COMPLETE')
if __name__=='__main__':unittest.main()
