INVALID_ULID = b"0" * 16

class TimeOverflowError(Exception):
    pass

def ulid_from_timestamp(timestamp):
    return b"0" * 16

def ulid_to_timestamp(ulid):
    return 0

def bytearray_to_base32(b):
    return ""

def base32_to_bytearray(s):
    return bytearray()

def ulid_at_time(timestamp):
    return "0" * 26

def ulid_now():
    return "0" * 26

def ulid_hex(ulid):
    return "0" * 32

def ulid_to_bytes(u):
    return b"0" * 16

def bytes_to_ulid(b):
    return "0" * 26

def bytes_to_ulid_or_none(b):
    return bytes_to_ulid(b) if b else None

def ulid_to_bytes_or_none(u):
    return ulid_to_bytes(u) if u else None
