import logging
import sys

STACKOVERFLOW_URL = 'https://stackoverflow.com/questions/tagged/{}?sort={}&page={}'
STACK_OVERFLOW_URL_Q = 'https://stackoverflow.com/search?q='
STACKOVERFLOW_QUESTION_URL = 'https://stackoverflow.com/questions/{}'
LOGGING_LEVEL = logging.DEBUG
LOGGING_HANDLERS = [logging.StreamHandler(sys.stdout)]

PROXIES_COUNTRIES = [
    'MO',
    'US',
    'NL',
    'JP',
    'US',
    'FR',
    'IT',
    'CA',
    'VN',
    'BR',
    'CA',
    'US',
    'IN',
    'SG',
    'JP',
    'NL',
    'CA',
    'BR',
    'GB',
    'JP'
]

f = open('proxy_list.txt', "r")
PAID_PROXY = f.read().split('\n')


PROXY_USERNAME = 'oyjEHM'
PROXY_PASSWORD = 'zEBuDW'

PROXY_TIMEOUT = 1
