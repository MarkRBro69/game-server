from frontend_service import settings

env = settings.ENV

GAME_SERVICE_PROTOCOL = 'http://'
GAME_SERVICE_HOST = env('GAME_SERVICE_HOST')
GAME_SERVICE_PORT = env('GAME_SERVICE_PORT')

GAME_SERVICE_PREFIX = 'gam/'
GAME_API_VERSION = 'api/v1/'

GAME_WS_VERSION = 'ws/'

GAME_LOBBY = 'game/'

GAME_API = ''.join([
    GAME_SERVICE_PROTOCOL,
    GAME_SERVICE_HOST,
    ':',
    GAME_SERVICE_PORT,
    '/',
    GAME_SERVICE_PREFIX,
    GAME_API_VERSION,
])

GAME_WS = ''.join([GAME_SERVICE_PROTOCOL, GAME_SERVICE_HOST, GAME_WS_VERSION])


def get_game_lobby_url():
    return f'{GAME_WS}{GAME_LOBBY}'
