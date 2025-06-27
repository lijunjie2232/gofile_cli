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
