from unittest import TestCase
from obihai_helper import ObihaiHelper


class TestObihaiHelper(TestCase):
    def test_add_caller_to_history(self):
        config_folder = "./"
        self.helper = ObihaiHelper(config_folder)
        self.helper.add_caller_to_history("port2", "11234567891", "John Smith", 1, "12:23:45 06/21")
        self.helper.add_caller_to_history("port2", "11234567890", "John Smith", 1, "12:23:45 06/22")
        self.helper.add_caller_to_history("port2", "11234567890", "John Smith", 1, "12:23:45 06/23")
        self.helper.add_caller_to_history("port2", "11234567890", "John Smith", 1, "12:23:45 06/24")


class TestObihaiHelper(TestCase):
    def test_get_caller_name_from_opencnam(self):
        config_folder = "./"
        self.helper = ObihaiHelper(config_folder)
        self.helper.get_caller_name_from_opencnam("11234567890")
