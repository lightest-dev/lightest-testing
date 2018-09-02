import socket
import sys
import requests
import time
import os
import shutil
import checker
import json


class server():
    def __init__(self, args):
        self.api_server = ""
        self.max_tries = 5
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('localhost', 10000)
        self.sock.bind(self.server_address)
        self.filename = ""
        self.code_upload = ""
        self.memory = 0
        self.time = 0
        self.tests_count = 0
        self.checker_id = 0
        self.checker_folder = "checkers"
        self.code_checker = checker.code_checker(self.checker_folder)

    def listen(self):
        self.sock.listen(1)
        while True:
            self.connection, self.client_address = self.sock.accept()
            try:
                self.read_data(self.connection)
            finally:
                self.connection.close()

    def read_data(self, connection):
        f = open("tempfile", "wb+")
        toread = 0
        started = False
        type = 0
        buf = bytearray(16)
        view = memoryview(buf)
        while True:
            length = self.sock.recv_into(view, 16)
            if length:
                if toread == 0:
                    if started:
                        self.process_data(type)
                        started = False
                        f = open("tempfile", "wb+")
                    started = True
                    toread = int.from_bytes(view[:4], signed=True)
                    type = view[4]
                    f.write(view[5:length])
                    toread = toread + 1 - length
                f.write(view)
                toread = toread - length
            else:
                return

    def process_data(self, type):
        # json or name:{filename}
        if type == 1:
            str = ""
            with open('tempfile', 'r') as myfile:
                str = myfile.read().replace('\n', '')
            if str.startswith("name:"):
                self.filename = str[5:]
            elif str.startswith("{"):
                self.parse_json(str)
        elif type == 2:
            os.rename("tempfile", os.path.join(
                self.code_upload, self.filename))
            if self.filename.startswith("code"):
                self.check(self.filename)

    def check(self, path):
        tests_count = 0
        compile_result = self.code_checker.compile(
            os.path.join(self.code_upload, path))
        if compile_result["error"]:
            result = {
                "failedTests": tests_count,
                "successfulTests": 0,
                "message": compile_result["error"],
                "status": "Compilation error",
                "type": "Code",
                "uploadId": self.code_upload
            }
            self.send_result(result)
            return
        # check files
        return

    def send_result(self, data, tries=0):
        r = requests.post(self.api_server, json=data)
        if r.status_code != 200:
            if tries == self.max_tries:
                return
            time.sleep(1)
            self.send_result(data, tries + 1)
        return

    def parse_json(self, text):
        in_json = json.loads(text)
        if "type" in in_json:
            self.parse_upload(in_json)
        else:
            self.parse_checker(in_json)

    def parse_checker(self, checker_json):
        path = os.path.join(self.checker_folder, checker_json["id"])
        f = open(path, "w+")
        f.write(checker_json["code"])
        result = self.code_checker.compile_checker(checker_json["id"])
        self.send_result(result)

    def parse_upload(self, upload_json):
        self.code_upload = upload_json["uploadId"]
        self.memory = upload_json["memory_limit"]
        self.time = upload_json["timeLimit"]
        self.tests_count = upload_json["testsCount"]
        self.checker_id = upload_json["checker_id"]
