from unittest import TestCase
from obihai_helper import ObihaiHelper
from obihai_scan import ObihaiScan
from obihai_syslog import ObihaiSyslog


class TestObihaiSyslog(TestCase):
    def test_handle_incoming_data(self):
        config_folder = "./"
        self.helper = ObihaiHelper(config_folder)
        self.obiscan = ObihaiScan(self.helper)
        self.syslog = ObihaiSyslog(self.helper, self.obiscan)

        data_bad1 = "<7> [SLIC]:Slic#0 OFFsaf HOOK"
        data_bad2 = "<7> fdgdgf[SLIC]:Slic#0 OFFsaf HOOK"
        self.syslog.handle_incoming_data(data_bad1)
        self.syslog.handle_incoming_data(data_bad2)

        data_hook_status1 = "<7> [SLIC]:Slic#0 OFF HOOK"
        data_hook_status2 = "<7> [SLIC]:Slic#0 ONHOOK"
        self.syslog.handle_incoming_data(data_hook_status1)
        self.syslog.handle_incoming_data(data_hook_status2)

        data_inbound1 = "<7> [SLIC] CID to deliver: 'John Smith' 11234567890"
        data_inbound2 = "<7> [SLIC] CID to deliver: 'Smith John' 11234567890"
        self.syslog.handle_incoming_data(data_inbound1)
        self.syslog.handle_incoming_data(data_inbound2)

        data_outbound1 = "<7> CCTL:NewCallOn Term 10[1] ->11234567890,11234567890"
        data_outbound2 = "<7> CCTL:NewCallOn Term 10[1] ->+11234567890,+11234567890"
        self.syslog.handle_incoming_data(data_outbound1)
        self.syslog.handle_incoming_data(data_outbound2)

