import re


def strip_and_lowercase(value):
    return re.sub(r'\W+', '', value).lower()
