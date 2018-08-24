import socket
import sys
import requests
import time
import os
import shutil
import checker


class server():
    def __init__(self, args):
        self.api_server = ""
        self.max_tries = 5
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('localhost', 10000)
        self.sock.bind(self.server_address)
        self.filename = ""
        self.code_upload = ""
        self.extension = ""
        self.memory = 0
        self.time = 0

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
        # code_upload:{upload.UploadId}
        # code.{upload.Language.Extension}
        # name:{filename}
        if type == 1:
            str = ""
            with open('tempfile', 'r') as myfile:
                str = myfile.read().replace('\n', '')
            if str.startswith("name:"):
                self.filename = str[5:]
            elif str.startswith("code_upload:"):
                if self.code_upload:
                    shutil.rmtree(self.code_upload, True)
                self.code_upload = str[12:]
                os.mkdir(self.code_upload, 700)
            elif str.startswith("code"):
                self.filename = str
                _, file_extension = os.path.splitext(str)
                self.extension = file_extension
                self.check(self.filename)
            elif str.startswith("time:"):
                self.time = int(str[5:])
            elif str.startswith("memory:"):
                self.memory = int(str[7:])
        elif type == 2:
            os.rename("tempfile", os.path.join(
                self.code_upload, self.filename))

    def check(self, path):
        tests_count = 0
        compile_result = checker.compile(os.path.join(self.code_upload, path))
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
