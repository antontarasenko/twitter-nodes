__author__ = 'Anton'

TW_API_KEY = "" # aka Consumer key
TW_API_SECRET = "" # aka Consumer secret
TW_ACCESS_TOKEN = "" # aka Token key
TW_TOKEN_SECRET = ""

try:
   from config_dev import *
except ImportError:
   pass
