import hashlib
import uuid

from django.conf import settings


def MD5(string):
    hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_object.update(string.encode('utf-8'))
    return hash_object.hexdigest()


# 用于生成随机字符串，作为上传图片名
def uid(string):
    data = "{}-{}".format(str(uuid.uuid4()), string)
    return MD5(data)
