import hashlib


def calculate_md5(file_path, md5Sum=""):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    if md5Sum:
        return hash_md5.hexdigest() == md5Sum
    return hash_md5.hexdigest()
