import socket
import sys
import requests
import time
import os
import shutil

api_server = ""
max_tries = 5
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10000)
sock.bind(server_address)
code_upload = ""
extension = ""

sock.listen(1)

while True:
    connection, client_address = sock.accept()
    try:
        read_data(connection)
    finally:
        connection.close()


def read_data(connection):
    f = open("tempfile", "wb+")
    toread = 0
    started = False
    type = 0
    buf = bytearray(16)
    view = memoryview(buf)
    while True:
        length = sock.recv_into(view, 16)
        if length:
            if toread == 0:
                if started:
                    process_data(type)
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


def process_data(type):
    # code_upload:{upload.UploadId}
    # code{upload.Language.Extension}
    # name:{filename}
    if type == 1:
        str = ""
        with open('tempfile', 'r') as myfile:
            str = myfile.read().replace('\n', '')
        if str.startswith("name:"):
            filename = str[5:]
        elif str.startswith("code_upload:"):
            global code_upload
            if code_upload:
                shutil.rmtree(code_upload, True)
            code_upload = str[12:]
            os.mkdir(code_upload, 700)
        elif str.startswith("code"):
            filename = str
            _, file_extension = os.path.splitext(str)
            global extension
            extension = file_extension
            check(filename)
    elif type == 2:
        os.rename("tempfile", os.path.join(code_upload, filename))


def compile(path):
    return


def check(path):
    if not compile(path):
        # send compilation error
        return
    # check files
    return


def send_result(data, tries=0):
    r = requests.post(api_server, json=data)
    if r.status_code != 200:
        if tries == max_tries:
            return
        time.sleep(1)
        send_result(data, tries + 1)
    return
