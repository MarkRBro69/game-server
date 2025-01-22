import environ
import config

env = environ.Env()
env.read_env(config.ENV_PATH)

GAME_SERVICE_PROTOCOL = 'https://'
GAME_SERVICE_HOST = env('GAME_SERVICE_HOST')
GAME_SERVICE_PORT = env('GAME_SERVICE_PORT')

GAME_SERVICE_PREFIX = 'gam/'
GAME_API_VERSION = 'api/v1/'

GAME_WS_VERSION = 'ws/'

GAME_LOBBY = 'game/'

GAME_API = ''.join([
    GAME_SERVICE_PROTOCOL,
    GAME_SERVICE_HOST,

    GAME_SERVICE_PORT,
    '/',
    GAME_SERVICE_PREFIX,
    GAME_API_VERSION,
])

GAME_WS = ''.join([GAME_SERVICE_PROTOCOL, GAME_SERVICE_HOST, GAME_WS_VERSION])


def get_game_lobby_url():
    return f'{GAME_WS}{GAME_LOBBY}'
