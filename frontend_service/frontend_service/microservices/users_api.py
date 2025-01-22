import environ
import config

env = environ.Env()
env.read_env(config.ENV_PATH)

USERS_SERVICE_PROTOCOL = 'http://'
USERS_SERVICE_HOST = env('USERS_SERVICE_HOST')
USERS_SERVICE_PORT = env('USERS_SERVICE_PORT')

USERS_SERVICE_PREFIX = 'usr/'
USERS_API_VERSION = 'api/v1/'

USERS_REGISTER = 'register_user/'
USERS_LOGIN = 'login/'

USERS_API = ''.join([
    USERS_SERVICE_PROTOCOL,
    USERS_SERVICE_HOST,

    USERS_SERVICE_PORT,
    '/',
    USERS_SERVICE_PREFIX,
    USERS_API_VERSION,
])


def get_users_registration_url():
    return f'{USERS_API}{USERS_REGISTER}'


def get_users_login_url():
    return f'{USERS_API}{USERS_LOGIN}'
