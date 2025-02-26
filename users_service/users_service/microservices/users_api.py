from django.conf import settings

env = settings.ENV

USERS_SERVICE_HOST = env('USERS_SERVICE_HOST')
USERS_SERVICE_PORT = env('USERS_SERVICE_PORT')

USERS_SERVICE_PREFIX = 'usr/'
USERS_API_VERSION = 'api/v1/'

USERS_REGISTER = 'register_user/'
USERS_LOGIN = 'login/'
USERS_ADD_WIN = 'add_win/'
USERS_ADD_LOSS = 'add_loss/'
USERS_DRAW = 'add_draw/'
USERS_CHANGE_RATING = 'change_rating/'
USERS_GET_RATING = 'get_rating/'
USERS_GET_PROFILE = 'get_profile/'
USERS_GET_USER = 'get_user/'
USERS_CREATE_CHARACTER = 'create_character/'
USERS_GET_USER_CHARACTERS = 'get_user_characters/'

RUNNING = env('RUNNING')
if RUNNING == 'railway':
    USERS_SERVICE_PROTOCOL = 'https://'

    USERS_API = ''.join([
        USERS_SERVICE_PROTOCOL,
        USERS_SERVICE_HOST,
        '/',
        USERS_SERVICE_PREFIX,
        USERS_API_VERSION,
    ])
else:
    USERS_SERVICE_PROTOCOL = 'http://'

    USERS_API = ''.join([
        USERS_SERVICE_PROTOCOL,
        USERS_SERVICE_HOST,
        ':',
        USERS_SERVICE_PORT,
        '/',
        USERS_SERVICE_PREFIX,
        USERS_API_VERSION,
    ])


def get_users_registration_url():
    return f'{USERS_API}{USERS_REGISTER}'


def get_users_login_url():
    return f'{USERS_API}{USERS_LOGIN}'


def get_users_add_win_url():
    return f'{USERS_API}{USERS_ADD_WIN}'


def get_users_add_loss_url():
    return f'{USERS_API}{USERS_ADD_LOSS}'


def get_users_add_draw_url():
    return f'{USERS_API}{USERS_DRAW}'


def get_users_change_rating_url():
    return f'{USERS_API}{USERS_CHANGE_RATING}'


def get_users_get_rating_url():
    return f'{USERS_API}{USERS_GET_RATING}'


def get_users_get_profile_url():
    return f'{USERS_API}{USERS_GET_PROFILE}'


def get_users_get_user_url():
    return f'{USERS_API}{USERS_GET_USER}'


def get_users_create_character_url():
    return f'{USERS_API}{USERS_CREATE_CHARACTER}'


def get_users_user_characters_url():
    return f'{USERS_API}{USERS_GET_USER_CHARACTERS}'
