USERS_SERVICE_PROTOCOL = 'http://'
USERS_SERVICE_HOST = '127.0.0.2:8002/'

USERS_SERVICE_PREFIX = 'usr/'
USERS_API_VERSION = 'api/v1/'

USERS_REGISTER = 'register_user/'


def get_users_registration_url():
    return f'{USERS_SERVICE_PROTOCOL}{USERS_SERVICE_HOST}{USERS_SERVICE_PREFIX}{USERS_API_VERSION}{USERS_REGISTER}'
