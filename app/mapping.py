from flask import json


with open("mappings/services.json") as services:
    SERVICES_MAPPING = json.load(services)
