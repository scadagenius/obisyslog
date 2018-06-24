import datetime
import json
import os
from collections import OrderedDict

import yaml  # this needs package called PyYAML

from requests import post


class ObihaiHelper:
    log_level_debug = 1
    log_level_info = 2
    log_level_warning = 3
    log_level_error = 4
    log_level_critical = 5
    max_supported_obihai_ports = 2

    def __init__(self, config_folder):
        self.config_folder = config_folder
        self.config = yaml.load(open(self.config_folder + 'config.yaml'))

        self.log_level = 2
        if self.config["syslog"]["logs"]["level"] == "debug":
            self.log_level = 1
        elif self.config["syslog"]["logs"]["level"] == "info":
            self.log_level = 2
        elif self.config["syslog"]["logs"]["level"] == "warning":
            self.log_level = 3
        elif self.config["syslog"]["logs"]["level"] == "error":
            self.log_level = 4
        elif self.config["syslog"]["logs"]["level"] == "critical":
            self.log_level = 5

        self.log_folder = self.config_folder + "logs/"
        self.syslog_log = self.log_folder + self.config["syslog"]["logs"]["syslog_log"]
        self.monitor_log = self.log_folder + self.config["syslog"]["logs"]["monitor_log"]
        self.phone_history_file = self.config_folder + "phone_history.json"
        self.phone_book_file = self.config_folder + "phone_book.json"
        self.show_history = self.config["home-assistant"]["show_history"]
        self.keep_history = self.config["syslog"]["keep_history"]

        if not os.path.exists(self.log_folder):
            os.makedirs(self.config_folder + "logs")
            self.print(self.log_level_info, "ObihaiHelper:__init__(): Creating folder: " + self.log_folder)

        self.update_ha_phone_history()

    def get_caller_name_from_phone_book(self, port_str, caller_number, call_date_time):
        self.print(self.log_level_debug, "ObihaiHelper:gcnfpb(): enter")
        json_phone_book = self.load_phone_book()
        item = json_phone_book.get(caller_number)
        if item is not None:
            caller_name = item["Name"]
        else:
            caller_name = self.get_caller_name_from_opencnam(caller_number)
            json_phone_book[caller_number] = {
                "Name": caller_name,
                "Port": port_str,
                "DateTime": call_date_time
            }
            self.save_phone_book(json_phone_book)
        self.print(self.log_level_debug, "ObihaiHelper:gcnfpb(): exit")
        return caller_name

    def add_caller_to_history(self, port_str, caller_number, caller_name, call_direction, call_date_time):
        self.print(self.log_level_debug, "ObihaiHelper:acth(): enter")
        try:
            json_phone_history = self.load_history_file()
            latest_key = self.get_latest_key(json_phone_history)
            json_phone_history[str(latest_key + 1)] = {
                "Name": caller_name,
                "Number": caller_number,
                "Type": call_direction,
                "Port": port_str,
                "DateTime": call_date_time
            }
            json_phone_history = self.trim_history_file(json_phone_history)
            self.save_history_file(json_phone_history)

            # Add to phone book if doesn't exist
            self.get_caller_name_from_phone_book(port_str, caller_number, call_date_time)
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:acth():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:acth(): exit")

    def load_phone_book(self):
        self.print(self.log_level_debug, "ObihaiHelper:lpb(): enter")
        json_phone_book = self.load_json_file(self.phone_book_file)
        self.print(self.log_level_debug, "ObihaiHelper:lpb(): exit")
        return json_phone_book

    def save_phone_book(self, json_phone_book):
        self.print(self.log_level_debug, "ObihaiHelper:spb(): enter")
        self.save_json_file(self.phone_book_file, json_phone_book)
        self.print(self.log_level_debug, "ObihaiHelper:spb(): exit")

    def load_history_file(self):
        self.print(self.log_level_debug, "ObihaiHelper:lhf(): enter")
        json_phone_history = self.load_json_file(self.phone_history_file)
        self.print(self.log_level_debug, "ObihaiHelper:lhf(): exit")
        return json_phone_history

    def save_history_file(self, json_phone_history):
        self.print(self.log_level_debug, "ObihaiHelper:uhf(): enter")
        self.save_json_file(self.phone_history_file, json_phone_history)
        self.print(self.log_level_debug, "ObihaiHelper:uhf(): exit")

    def trim_history_file(self, json_phone_history):
        self.print(self.log_level_debug, "ObihaiHelper:thf(): enter")
        if len(json_phone_history) > self.keep_history:
            latest_key = self.get_latest_key(json_phone_history)
            key_to_delete = latest_key - self.keep_history
            try:
                while len(json_phone_history) > self.keep_history:
                    del json_phone_history[str(key_to_delete)]
                    key_to_delete = key_to_delete - 1
            except:
                pass
        self.print(self.log_level_debug, "ObihaiHelper:thf(): exit")
        return json_phone_history

    def get_latest_key(self, json_phone_history):
        self.print(self.log_level_debug, "ObihaiHelper:glk(): enter")
        latest_key = 0
        for key, value in json_phone_history.items():
            if latest_key < int(key):
                latest_key = int(key)
        self.print(self.log_level_debug, "ObihaiHelper:glk(): exit")
        return latest_key

    def load_json_file(self, file_to_load):
        self.print(self.log_level_debug, "ObihaiHelper:ljf(): enter")
        json_data = OrderedDict()
        try:
            if os.path.exists(file_to_load):
                with open(file_to_load, "r") as file_handle_read:
                    json_data = json.load(file_handle_read, object_pairs_hook=OrderedDict)
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:ljf():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:ljf(): exit")
        return json_data

    def save_json_file(self, file_to_save, json_data):
        self.print(self.log_level_debug, "ObihaiHelper:sjf(): enter")
        try:
            with open(file_to_save, "w") as file_handle_write:
                file_handle_write.write(json.dumps(json_data, indent=4))
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:sjf():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:sjf(): exit")

    def get_log_level_to_string(self, log_level):
        log_level_str = ": "
        if log_level == self.log_level_debug:
            log_level_str = ":debug: "
        elif log_level == self.log_level_info:
            log_level_str = ":info: "
        elif log_level == self.log_level_warning:
            log_level_str = ":warn: "
        elif log_level == self.log_level_error:
            log_level_str = ":error: "
        elif log_level == self.log_level_critical:
            log_level_str = ":critical: "
        return log_level_str

    def log_data(self, message_data):
        self.print(self.log_level_debug, "ObihaiHelper:ld(): enter")
        try:
            log_file_name = self.syslog_log + "-" + datetime.datetime.now().strftime('%Y-%m-%d') + ".log"
            with open(log_file_name, "a") as log_file:
                log_file.write(message_data)
        except Exception as e:
            self.print(self.log_level_error, "ErxHelper:log_data():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:ld(): exit")

    def print(self, log_level, str_print):
        if self.log_level > log_level:
            return
        try:
            log_file_name = self.monitor_log + "-" + datetime.datetime.now().strftime('%Y-%m-%d') + ".log"
            log_str = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3] + \
                      self.get_log_level_to_string(log_level) + str_print

            print(log_str)
            with open(log_file_name, "a") as log_file:
                log_file.write(log_str + "\n")
        except Exception as e:
            print(datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3] + " : ObihaiHelper:print():Exception: " + str(e))

    def update_ha_sensor(self, entity, state_str, attributes):
        self.print(self.log_level_debug, "ObihaiHelper:uhs(): enter")
        try:
            base_url_post = self.config["home-assistant"]["url"] + "/api/states/" + entity + "?api_password=" + \
                            self.config["home-assistant"]["password"]
            # for safety reason don't print following debug information as it may contain sensitive information
            # for users who has public facing Home Assistant
            # self.print(self.log_level_debug, "ObihaiHelper:uhs(): url: " + base_url_post)

            payload = {"state": state_str, "attributes": attributes}
            self.print(self.log_level_info, "ObihaiHelper:uhs(): payload: " + str(json.dumps(payload)))

            response = post(base_url_post, data=json.dumps(payload))
            self.print(self.log_level_info, "ObihaiHelper:uhs(): response: " + str(response.text))
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:uhs():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:uhs(): exit")

    def ha_service_notify(self, whom, message):
        self.print(self.log_level_debug, "ObihaiHelper:hsn(): enter")
        try:
            base_url_post = self.config["home-assistant"]["url"] + "/api/services/" + whom + "?api_password=" + \
                            self.config["home-assistant"]["password"]

            payload = {"message": message}
            self.print(self.log_level_info, "ObihaiHelper:hsn(): payload: " + str(json.dumps(payload)))

            response = post(base_url_post, data=json.dumps(payload))
            self.print(self.log_level_info, "ObihaiHelper:hsn(): response: " + str(response.text))
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:uhs():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:hsn(): exit")

    def update_ha_phone_history(self):
        self.print(self.log_level_debug, "ObihaiHelper:uhph(): enter")
        try:
            json_phone_history = self.load_history_file()
            item_index = str(self.get_latest_key(json_phone_history))
            for index in range(1, self.show_history + 1):
                if index <= len(json_phone_history):
                    entity = "sensor.phone_details_" + str(index)
                    state_str = json_phone_history[item_index]["Name"] + " (" + \
                                json_phone_history[item_index]["Number"] + ")"
                    attributes = {
                        "friendly_name": json_phone_history[item_index]["DateTime"],
                        "type": json_phone_history[item_index]["Type"]
                    }
                    if json_phone_history[item_index]["Type"] == "Inbound":
                        icon_attributes = {"icon": "mdi:phone-incoming"}
                    else:
                        icon_attributes = {"icon": "mdi:phone-outgoing"}
                    attributes.update(icon_attributes)
                    self.update_ha_sensor(entity, state_str, attributes)
                    item_index = str(int(item_index) - 1)
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:uhph():Exception:" + str(e))
        self.print(self.log_level_debug, "ObihaiHelper:uhph(): exit")

    def get_caller_name_from_opencnam(self, phone_number):
        self.print(self.log_level_debug, "ObihaiHelper:gcnfo(): enter")

        caller_name = ""
        try:
            base_url = self.config["opencnam"]["base_url"]
            sid = self.config["opencnam"]["sid"]
            token = self.config["opencnam"]["token"]
            if base_url != "" and sid != "" and token != "":
                phone_number = phone_number.replace('(', '')
                phone_number = phone_number.replace(')', '')
                phone_number = phone_number.replace('-', '')
                phone_number = phone_number.replace('+', '')
                phone_number = phone_number.replace(' ', '')
                base_url_post = base_url + phone_number + sid + token
                response = post(base_url_post)
                self.print(self.log_level_info, "ObihaiHelper:gcnfo():requesting: " + phone_number)
                self.print(self.log_level_info, "ObihaiHelper:gcnfo():response: " + response.text)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    caller_name = data['name'].strip()
                else:
                    self.print(self.log_level_info, "ObihaiHelper:gcnfo():status code: " +
                               str(response.status_code) + " for number: " + phone_number)
            else:
                self.print(self.log_level_info, "ObihaiHelper:gcnfo():opencnam not configured")
        except Exception as e:
            self.print(self.log_level_error, "ObihaiHelper:gcnfo():Exception:" + str(e))

        self.print(self.log_level_debug, "ObihaiHelper:gcnfo(): exit")
        return caller_name
