import json

OPT_APPEND_NEWLINE = 0
OPT_NON_STR_KEYS = 0
OPT_SORT_KEYS = 0
JSONDecodeError = ValueError

class Fragment(bytes):
    pass

OPT_PASSTHROUGH_DATACLASS = 0
OPT_PASSTHROUGH_DATETIME = 0

def dumps(obj, option=None, default=None):
    text = json.dumps(obj, default=default)
    if option == OPT_APPEND_NEWLINE:
        text += "\n"
    return text.encode()

def loads(data):
    if isinstance(data, (bytes, bytearray)):
        data = data.decode()
    return json.loads(data)
