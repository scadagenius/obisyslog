import sys

from obihai_helper import ObihaiHelper
from obihai_scan import ObihaiScan
from obihai_syslog import ObihaiSyslog


class ObihaiMonitor:
    def __init__(self, config_folder):
        self.helper = ObihaiHelper(config_folder)
        self.helper.print(self.helper.log_level_info, "ObihaiMonitor: Starting Obihai Monitor")

        self.obiscan = ObihaiScan(self.helper)
        self.obiscan.scan_call_status()
        self.obiscan.start()

        self.syslog = ObihaiSyslog(self.helper, self.obiscan)
        while True:
            try:
                self.helper.print(self.helper.log_level_debug, "ObihaiMonitor: Start obihai syslog monitor loop")
                self.syslog.monitor()
            except Exception as e:
                self.helper.print(self.helper.log_level_error, "ObihaiMonitor: Exception: " + str(e))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
        if not root_path.endswith("/"):
            root_path = root_path + "/"
    else:
        root_path = "/config/"
    print("Config folder: " + root_path)
    main_object = ObihaiMonitor(root_path)
