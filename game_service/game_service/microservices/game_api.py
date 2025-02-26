from game_service import settings

env = settings.ENV

GAME_SERVICE_HOST = env('GAME_SERVICE_HOST')
GAME_SERVICE_PORT = env('GAME_SERVICE_PORT')

GAME_SERVICE_PREFIX = 'gam/'
GAME_API_VERSION = 'api/v1/'

GAME_WS_VERSION = 'ws/'

GAME_GLOBAL = 'global/'
GAME_LOBBY = 'game/'

GAME_AUTH_TOKEN = 'get_auth_token/'

RUNNING = env('RUNNING')
if RUNNING == 'railway':
    GAME_SERVICE_PROTOCOL = 'https://'
    GAME_SERVICE_WS_PROTOCOL = 'wss://'

    GAME_API = ''.join([
        GAME_SERVICE_PROTOCOL,
        GAME_SERVICE_HOST,
        '/',
        GAME_SERVICE_PREFIX,
        GAME_API_VERSION,
    ])

    GAME_WS = ''.join([
        GAME_SERVICE_WS_PROTOCOL,
        GAME_SERVICE_HOST,
        '/',
        GAME_WS_VERSION,
    ])

else:
    GAME_SERVICE_PROTOCOL = 'http://'
    GAME_SERVICE_WS_PROTOCOL = 'ws://'

    GAME_API = ''.join([
        GAME_SERVICE_PROTOCOL,
        GAME_SERVICE_HOST,
        ':',
        GAME_SERVICE_PORT,
        '/',
        GAME_SERVICE_PREFIX,
        GAME_API_VERSION,
    ])

    GAME_WS = ''.join([
        GAME_SERVICE_WS_PROTOCOL,
        GAME_SERVICE_HOST,
        ':',
        GAME_SERVICE_PORT,
        '/',
        GAME_WS_VERSION,
    ])


def get_global_lobby_url():
    return f'{GAME_WS}{GAME_GLOBAL}'


def get_game_lobby_url():
    return f'{GAME_WS}{GAME_LOBBY}'


def get_game_auth_token_url():
    return f'{GAME_API}{GAME_AUTH_TOKEN}'
