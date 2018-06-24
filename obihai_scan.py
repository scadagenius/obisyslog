import time
import datetime
import requests
import xml.etree.ElementTree
import re
from requests.auth import HTTPDigestAuth
from threading import Thread


class ObihaiScan:
    def __init__(self, helper):
        self.helper = helper
        self.poll_interval = int(self.helper.config["obihai"]["poll_interval"])

    def start(self):
        self.helper.print(self.helper.log_level_debug, "ObihaiScan:start(): enter")

        if self.poll_interval > 0:
            self.helper.print(self.helper.log_level_info,
                              "ObihaiScan:start(): polling every {0} seconds".format(str(self.poll_interval)))
            thread = Thread(target=self.thread_scan_obihai_system)
            thread.start()
        else:
            self.helper.print(self.helper.log_level_info,
                              "ObihaiScan:start(): No polling as interval is {0} seconds".format(
                                  self.helper.config["obihai"]["poll_interval"]))

        self.helper.print(self.helper.log_level_debug, "ObihaiScan:start(): exit")

    def thread_scan_obihai_system(self):
        while True:
            try:
                self.helper.print(self.helper.log_level_debug, "ObihaiScan:tsos(): enter")
                reboot_required, up_time, system_time, software_version, statuses = self.scan_full_system_status()
                self.helper.print(self.helper.log_level_info, "ObihaiScan:tsos(): summary: "
                                  + "Obihai System Reboot: " + reboot_required + ", Up Time: " + up_time
                                  + ", System Time: " + system_time + ", Software Version: " + software_version +
                                  ", Statuses: " + statuses)
                self.helper.print(self.helper.log_level_debug, "ObihaiScan:tsos(): exit")
                time.sleep(self.poll_interval)
            except Exception as e:
                self.helper.print(self.helper.log_level_error, "ObihaiScan:tsos(): exception: " + str(e))

    def get_base_url(self, req_type):
        url_str = "http://" + self.helper.config["obihai"]["username"] + ":" + \
                  self.helper.config["obihai"]["password"] + "@" + self.helper.config["obihai"]["ip"]
        if req_type == "system_status":
            url_str = url_str + "/DI_S_.xml"
        elif req_type == "call_status":
            url_str = url_str + "/callstatus.htm"
        else:
            self.helper.print(self.helper.log_level_error, "ObihaiScan:gbu(): invalid base url request: " + req_type)

        return url_str

    def get_http_auth(self):
        return HTTPDigestAuth(self.helper.config["obihai"]["username"], self.helper.config["obihai"]["password"])

    def scan_full_system_status(self):
        self.helper.print(self.helper.log_level_debug, "ObihaiScan:sfss(): enter")
        reboot_required = "No"
        up_time = ""
        system_time = ""
        software_version = ""
        statuses = ""

        try:
            base_url_for_system_status = self.get_base_url("system_status")
            self.helper.print(self.helper.log_level_debug, "ObihaiScan:sfss(): url: " + base_url_for_system_status)

            response = requests.get(base_url_for_system_status, auth=self.get_http_auth())
            self.helper.print(self.helper.log_level_debug, "ObihaiScan:sfss(): response:" + str(response))

            tree_root = xml.etree.ElementTree.fromstring(response.text)
            for models in tree_root.iter('model'):
                if models.attrib["reboot_req"] == "true":
                    reboot_required = "Yes"
                self.helper.print(self.helper.log_level_info,
                                  "ObihaiScan:sfss(): Obihi device needs reboot: " + reboot_required)
                break

            for params in tree_root.iter('parameter'):
                if params.attrib["name"] == "UpTime":
                    for attributes in params.iter('value'):
                        up_time = str(attributes.attrib["current"])
                        self.helper.print(self.helper.log_level_info, "ObihaiScan:sfss(): UpTime: " + up_time)
                        break
                elif params.attrib["name"] == "SystemTime":
                    for attributes in params.iter('value'):
                        system_time = str(attributes.attrib["current"])
                        self.helper.print(self.helper.log_level_info, "ObihaiScan:sfss(): SystemTime: " + system_time)
                        break
                elif params.attrib["name"] == "SoftwareVersion":
                    for attributes in params.iter('value'):
                        software_version = str(attributes.attrib["current"])
                        self.helper.print(self.helper.log_level_info,
                                          "ObihaiScan:sfss(): SoftwareVersion: " + software_version)
                        break
                elif params.attrib["name"] == "Status":
                    for attributes in params.iter('value'):
                        temp_str = str(attributes.attrib["current"])
                        if temp_str != "No Dongle" and temp_str != "Service Not Configured":
                            start = temp_str.find(' ')
                            if start != -1:
                                temp_str = temp_str[:start]
                            statuses += temp_str + "/"
                            self.helper.print(self.helper.log_level_info, "ObihaiScan:sfss(): Status: " + statuses)
                            break
        except Exception as e:
            self.helper.print(self.helper.log_level_error, "ObihaiScan:sfss(): exception: " + str(e))

        start = statuses.rfind("/")
        if start != -1:
            statuses = statuses[:start]

        # normalize spacing
        up_time = ' '.join(up_time.split())
        system_time = ' '.join(system_time.split())
        software_version = ' '.join(software_version.split())
        statuses = ' '.join(statuses.split())
        try:
            self.helper.update_ha_sensor("sensor.obihai_reboot_required", reboot_required,
                                         {"friendly_name": "Reboot Required", "icon": "mdi:phone-classic"})
            self.helper.update_ha_sensor("sensor.obihai_up_time", up_time, {"friendly_name": "Up Time",
                                                                            "icon": "mdi:timetable"})
            self.helper.update_ha_sensor("sensor.obihai_software_version", software_version,
                                         {"friendly_name": "Software Version", "icon": "mdi:application"})
            self.helper.update_ha_sensor("sensor.obihai_statuses", statuses,
                                         {"friendly_name": "Statuses", "icon": "mdi:heart-outline"})
            self.helper.update_ha_sensor("sensor.obihai_last_updated",
                                         datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                                         {"friendly_name": "Last Updated", "icon": "mdi:timetable"})
        except Exception as e:
            self.helper.print(self.helper.log_level_error, "ObihaiScan:sfss(): exception: " + str(e))

        self.helper.print(self.helper.log_level_debug, "ObihaiScan:sfss(): exit")
        return reboot_required, up_time, system_time, software_version, statuses

    def scan_call_status(self):
        self.helper.print(self.helper.log_level_debug, "ObihaiScan:scs(): enter")
        call_status = "Idle"
        call_direction = ""
        caller_number = ""
        caller_name = ""
        caller_start_time = ""

        try:
            base_url_for_call_status = self.get_base_url("call_status")
            self.helper.print(self.helper.log_level_debug, "ObihaiScan:scs(): url: " + base_url_for_call_status)

            response = requests.get(base_url_for_call_status, auth=self.get_http_auth())
            self.helper.print(self.helper.log_level_debug, "ObihaiScan:scs(): response:" + str(response))

            lines = response.text
            start = lines.find("Number of Active Calls:")
            if start != -1:
                temp_str = lines[start + 24:]
                end = temp_str.find("</tr>")  # /td> is missing
                if end != -1:
                    call_status = str(temp_str[:end])
                    if call_status == "1":
                        start = lines.find("Inbound")
                        if start != -1:
                            call_direction = "Inbound"
                        else:
                            start = lines.find("Outbound")
                            if start != -1:
                                call_direction = "Outbound"
                        m = re.search("Peer Number<td>(.*)", lines)
                        if m:
                            temp_str = str(m.groups()[0])
                            end = temp_str.find("<td>")  # /td> is missing
                            if end != -1:
                                caller_number = temp_str[:end]
                        m = re.search("Peer Name<td>(.*)", lines)
                        if m:
                            temp_str = m.groups()[0]
                            end = temp_str.find("<td></tr>")  # /td> is missing
                            if end != -1:
                                caller_name = temp_str[:end]
                        m = re.search("Start Time<td>(.*)", lines)
                        if m:
                            temp_str = m.groups()[0]
                            end = temp_str.find("<td>")  # /td> is missing
                            if end != -1:
                                caller_start_time = temp_str[:end]

        except Exception as e:
            self.helper.print(self.helper.log_level_error, "ObihaiScan:scs(): exception: " + str(e))

        if call_status == "0":
            call_status = "Idle"
        call_direction = call_direction.strip()
        caller_number = caller_number.strip()
        caller_name = caller_name.strip()
        caller_start_time = caller_start_time.strip()
        caller_number = self.format_phone_number(caller_number)

        self.helper.print(self.helper.log_level_debug, "ObihaiScan:scs(): exit")
        return call_status, call_direction, caller_start_time, caller_name, caller_number

    def format_phone_number(self, phone_number):
        self.helper.print(self.helper.log_level_debug, "ObihaiScan:fpn(): enter")
        phone_number = phone_number.replace('(', '')
        phone_number = phone_number.replace(')', '')
        phone_number = phone_number.replace('-', '')
        phone_number = phone_number.replace('+', '')
        phone_number = phone_number.replace(' ', '')
        phone_number = phone_number.strip()
        if phone_number != "":
            if phone_number.startswith("011"):
                # remove IDD international dialing prefix so CNam can work to find the name
                phone_number = phone_number[3:]
            phone_number = "{}({}){}-{}".format(phone_number[:-10], phone_number[-10:-7], phone_number[-7:-4],
                                                phone_number[-4:])
        self.helper.print(self.helper.log_level_debug, "ObihaiScan:fpn(): exit")
        return phone_number
