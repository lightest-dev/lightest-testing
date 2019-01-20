import hashlib


def get_files_hash(*args):
    sha256_hash = hashlib.sha256()
    for file in args:
        with open(file, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    return str(sha256_hash.hexdigest())


def get_server_hash():
    result = get_files_hash('./server.py', './checker.py',
                            './models/upload.py', './models/sent_file.py',
                            './models/settings.py')
    return result


if __name__ == "__main__":
    hash = get_server_hash()
    print(hash)
