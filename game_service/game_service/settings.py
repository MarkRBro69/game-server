import environ
import config

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ENV = environ.Env()
if ENV.bool('DOCKER_ENV', default=False):
    ENV.read_env(BASE_DIR.parent / '.env.docker')  # Docker
else:
    ENV.read_env(BASE_DIR.parent / '.env.local')  # Local

SECRET_KEY = ENV('GAME_SERVICE_SECRET_KEY')

DEBUG = ENV.bool('DEBUG')

ALLOWED_HOSTS = ['127.0.0.3', 'localhost', 'game', 'game-production-2d31.up.railway.app']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'channels',

    'game_app.apps.GameAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'game_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'game_service.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGGING = config.LOGGING

ASGI_APPLICATION = "game_service.asgi.application"

REDIS_HOST = ENV('REDIS_HOST')
REDIS_PORT = ENV('REDIS_PORT')

RUNNING = ENV('RUNNING')
if RUNNING == 'railway':
    REDIS_USERNAME = ENV('REDIS_USERNAME')
    REDIS_PASSWORD = ENV('REDIS_PASSWORD')

    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"],
            },
        },
    }

else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(REDIS_HOST, REDIS_PORT)],
            },
        },
    }

CORS_ALLOWED_ORIGINS = [
    "https://game-production-2d31.up.railway.app",
    "http://localhost:5173",
]
