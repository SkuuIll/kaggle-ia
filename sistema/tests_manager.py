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
