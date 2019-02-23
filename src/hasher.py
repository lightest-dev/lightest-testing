import hashlib
from glob import glob


def get_files_hash(*args):
    sha256_hash = hashlib.sha256()
    for file in args:
        with open(file, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    return str(sha256_hash.hexdigest())


def get_server_hash():
    files = glob('**/*.py', recursive=True)
    files.extend(glob('**/*.json', recursive=True))
    result = get_files_hash(*files)
    return result


if __name__ == "__main__":
    hash = get_server_hash()
    print(hash)
