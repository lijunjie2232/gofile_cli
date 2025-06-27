import hashlib
from time import sleep, time
import re

AUTH_PATTERN = re.compile(r"https://gofile.io/login/(.*)\n")


def calculate_md5(file_path, md5Sum=""):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    if md5Sum:
        return hash_md5.hexdigest() == md5Sum
    return hash_md5.hexdigest()


def message_filter(MAIL_TM, account, waiting_time=120):
    start_time = time()
    while start_time + waiting_time > time():
        messages = MAIL_TM.get_messages(account)
        for msg in messages.hydra_member:
            if msg.isDeleted or msg.seen:
                continue
            content = MAIL_TM.get_message_by_id(
                message_id=msg.id,
                account=account,
            )
            result = AUTH_PATTERN.findall(content.text)
            if result:
                return result[0]
        sleep(5)


def convert_bytes_to_readable(size_bytes):
    units = ["B", "KB", "MB", "GB"]
    index = 0
    while size_bytes >= 1024.0 and index < len(units) - 1:
        size_bytes /= 1024.0
        index += 1
    bstr = f"{size_bytes:.2f}"
    while bstr.endswith("0"):
        bstr = bstr[:-1]
    if bstr.endswith("."):
        bstr = bstr[:-1]
    return f"{bstr} {units[index]}"
