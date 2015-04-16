import re


def strip_and_lowercase(value):
    return re.sub(r'[\s+|\W+]', '', value).lower()
