import datetime
import socket
import time

socket_receive_buffer = 4096


class ObihaiSyslog:
    def __init__(self, obihelper, obiscan):
        self.helper = obihelper
        self.obiscan = obiscan

    def monitor(self):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:monitor(): enter")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.helper.config["syslog"]["ip"], self.helper.config["syslog"]["port"]))
            while True:
                data, address = sock.recvfrom(socket_receive_buffer)
                self.handle_incoming_data(data.decode('utf-8'))
        except Exception as e:
            self.helper.print(self.helper.log_level_error, "ObihaiSyslog:monitor():Exception: " + str(e))
            time.sleep(60)
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:monitor(): exit")

    def handle_incoming_data(self, string_data):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:hid(): enter")

        time_stamp = datetime.datetime.now().strftime('%H:%M:%S')
        string_data = time_stamp + " ::: " + string_data
        self.helper.log_data(string_data)

        any_change, port_str, hook_status, call_direction, caller_name, caller_number = self.parse_message_data(
            string_data)
        if any_change:
            if hook_status != "":
                self.process_hook_change(hook_status, port_str)
            else:
                self.process_call_change(port_str, call_direction, caller_name, caller_number)
            self.helper.print(self.helper.log_level_info, "ObihaiSyslog:hid(): " + time_stamp + ", " + hook_status +
                              ", " + call_direction + ", " + caller_name + ", " + caller_number)
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:hid(): exit")

    def parse_message_data(self, message_data):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:pmd(): enter")

        call_direction = ""
        caller_name = ""
        caller_number = ""

        any_change, port, hook_status = self.is_hook_change(message_data)
        if not any_change:
            any_change, port, call_direction, caller_name, caller_number = self.is_inbound_call(message_data)
            if not any_change:
                any_change, port, call_direction, caller_name, caller_number = self.is_outbound_call(message_data)

        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:pmd(): exit")
        port_str = "port" + str(port)
        return any_change, port_str, hook_status, call_direction, caller_name, caller_number

    def get_config_friendly_name(self, port_str):
        return self.helper.config["obihai"]["monitor"][port_str]

    def process_hook_change(self, hook_status, port_str):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:phc(): enter")

        self.helper.update_ha_sensor("sensor.phone_status_" + port_str, hook_status,
                                     {
                                         "friendly_name": "Phone Status " + self.get_config_friendly_name(port_str),
                                         "icon": "mdi:phone-classic"
                                     })
        if hook_status == "On Hook":
            active_call_direction = "Idle"
            self.helper.update_ha_sensor("sensor.active_call_direction_" + port_str, active_call_direction,
                                         {
                                             "friendly_name": "Active Phone Status " +
                                                              self.get_config_friendly_name(port_str),
                                             "icon": "mdi:phone-classic"
                                         })

        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:phc(): exit")

    def process_call_change(self, port_str, call_direction, caller_name, caller_number):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:pcc(): enter")

        call_status, call_direction, caller_start_time, caller_name, caller_number = self.obiscan.scan_call_status()
        caller_number = self.obiscan.format_phone_number(caller_number)
        if call_status != "Idle":
            caller_name = self.helper.get_caller_name_from_phone_book(port_str, caller_number, caller_start_time)
            self.helper.update_ha_sensor("sensor.active_call_direction_" + port_str, call_direction,
                                         {
                                             "friendly_name": "Active Phone Status " + self.get_config_friendly_name(
                                                 port_str),
                                             "icon": "mdi:phone-classic"
                                         })

            call_time = caller_start_time + " " + datetime.datetime.now().strftime('%m/%d')
            self.helper.add_caller_to_history(port_str, caller_number, caller_name, call_direction, call_time)
            self.helper.update_ha_phone_history()
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:pcc(): exit")

    def get_config_hook_string(self, port_number):
        config_str = ""
        port_str = "port" + str(port_number)
        if port_str in self.helper.config["obihai"]["monitor"]:
            config_str = self.helper.config["obihai"][port_str]["onoffhook"]
        return config_str

    def is_hook_change(self, message_data):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:ihc(): enter")
        any_change = False
        hook_status = ""
        port = 1
        while port <= self.helper.max_supported_obihai_ports:
            str_to_match = self.get_config_hook_string(port)
            if str_to_match != "":
                start_index = message_data.find(str_to_match)
                if start_index != -1:
                    if message_data[start_index + 18:].startswith("ONHOOK"):
                        any_change = True
                        hook_status = "On Hook"
                    elif message_data[start_index + 18:].startswith("OFF HOOK"):
                        any_change = True
                        hook_status = "Off Hook"
                    break
            port = port + 1
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:ihc(): exit")
        return any_change, port, hook_status

    def get_config_inbound_string(self, port_number):
        config_str = ""
        port_str = "port" + str(port_number)
        if port_str in self.helper.config["obihai"]["monitor"]:
            config_str = self.helper.config["obihai"][port_str]["inbound"]
        return config_str

    def is_inbound_call(self, message_data):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:iic(): enter")
        any_change = False
        call_direction = ""
        caller_name = ""
        caller_number = ""
        port = 1
        while port <= self.helper.max_supported_obihai_ports:
            str_to_match = self.get_config_inbound_string(port)
            if str_to_match != "":
                start_index = message_data.find(str_to_match)
                if start_index != -1:
                    any_change = True
                    call_direction = "Inbound"
                    caller_name = message_data[start_index + 28:]
                    start_index = caller_name.find("'")
                    if start_index != -1:
                        temp_str = caller_name[start_index + 1:].strip()
                        caller_name = caller_name[:start_index]
                        caller_name = ' '.join(caller_name.split())  # normalize spaces
                        for c in temp_str:
                            if c.isdigit():
                                caller_number += c
                            else:
                                break
                        caller_number = self.obiscan.format_phone_number(caller_number)
                    break
            port = port + 1
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:iic(): exit")
        return any_change, port, call_direction, caller_name, caller_number

    def get_config_outbound_string(self, port_number):
        config_str = ""
        port_str = "port" + str(port_number)
        if port_str in self.helper.config["obihai"]["monitor"]:
            config_str = self.helper.config["obihai"][port_str]["outbound"]
        return config_str

    def is_outbound_call(self, message_data):
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:ioc(): enter")
        any_change = False
        call_direction = ""
        caller_name = ""
        caller_number = ""
        port = 1
        while port <= self.helper.max_supported_obihai_ports:
            str_to_match = self.get_config_outbound_string(port)
            if str_to_match != "":
                start_index = message_data.find(str_to_match)
                if start_index != -1:
                    any_change = True
                    call_direction = "Outbound"
                    temp_str = message_data[start_index + 32:].split(',')
                    caller_number = self.obiscan.format_phone_number(temp_str[0])
                    break
            port = port + 1
        self.helper.print(self.helper.log_level_debug, "ObihaiSyslog:ioc(): exit")
        return any_change, port, call_direction, caller_name, caller_number
