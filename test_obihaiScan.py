from unittest import TestCase

from obihai_helper import ObihaiHelper
from obihai_scan import ObihaiScan


class TestObihaiScan(TestCase):
    def test_scan_full_system_status(self):
        config_folder = "./"
        self.helper = ObihaiHelper(config_folder)
        self.obiscan = ObihaiScan(self.helper)

        print(self.obiscan.scan_full_system_status())

    def test_scan_call_status(self):
        config_folder = "./"
        self.helper = ObihaiHelper(config_folder)
        self.obiscan = ObihaiScan(self.helper)

        print(self.obiscan.scan_call_status())

    def test_format_phone_number(self):
        config_folder = "./"
        self.helper = ObihaiHelper(config_folder)
        self.obiscan = ObihaiScan(self.helper)

        phone_str = "1234567890"
        print(self.obiscan.format_phone_number(phone_str))
        phone_str = "0111234567890"
        print(self.obiscan.format_phone_number(phone_str))
