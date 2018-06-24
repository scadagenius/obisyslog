FROM python:3.6

RUN pip3 install requests PyYAML

ADD obihai_helper.py obihai_scan.py obihai_syslog.py main_obihai.py /

CMD ["python", "./main_obihai.py"]
