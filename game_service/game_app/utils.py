import json
import logging
import random
import string
from enum import Enum

import redis
import requests
from django.conf import settings
from django.core.cache import cache

from game_service.microservices.users_api import (
    get_users_add_win_url,
    get_users_add_loss_url,
    get_users_add_draw_url,
    get_users_change_rating_url,
    get_users_get_user_url,
    get_users_char_experience_url
)


logger = logging.getLogger('game_server')


class Commands(Enum):
    INVITE = '/invite'
    PRIVATE = '/private'
    MESSAGE = '/message'
    SEARCH = '/search'

    @staticmethod
    def get_values_set():
        return {command.value for command in Commands}


class ConsumerUtils:
    @staticmethod
    def parse_message(message):
        recipient = None
        parsed_message = ''
        if message.startswith('/'):
            split_message = message.split(' ', 1)
            command = split_message[0]
            if len(split_message) > 1:
                parsed_message = split_message[1]
            commands_values = Commands.get_values_set()

            try:
                parsed_command = Commands(command)
            except ValueError:
                return Commands.MESSAGE.value, message, recipient

            if parsed_command == Commands.PRIVATE or parsed_command == Commands.INVITE:
                recipient, parsed_message = ConsumerUtils.parse_recipient(parsed_message)
                return command, parsed_message, recipient

            if command in commands_values:
                return command, parsed_message, recipient
            else:
                return Commands.MESSAGE.value, message, recipient

        return Commands.MESSAGE.value, message, recipient

    @staticmethod
    def parse_recipient(message):
        parsed_message = ''
        split_message = message.split(' ', 1)
        recipient = split_message[0]
        if len(split_message) > 1:
            parsed_message = split_message[1]

        return recipient, parsed_message


class RedisServer:
    MAX_MESSAGES = 1000
    TTL = 3600 * 24
    TIME_TO_SEARCH = '30'

    def __init__(self):
        if settings.RUNNING == 'railway':
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                username=settings.REDIS_USERNAME,
                password=settings.REDIS_PASSWORD,
            )
        else:
            self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

    def add_channel(self, username, channel_name):
        channel_key = f'channel_{username}'
        self.redis.set(channel_key, channel_name, ex=RedisServer.TTL)

    def get_channel(self, username):
        channel_key = f'channel_{username}'
        return self.redis.get(channel_key)

    def delete_channel(self, username):
        channel_key = f'channel_{username}'
        self.redis.delete(channel_key)

    def add_private_message(self, recipient, message):
        user_private = f'private_{recipient}'
        json_massage = json.dumps(message)
        self.redis.rpush(user_private, json_massage)
        self.redis.expire(user_private, RedisServer.TTL)

    def delete_private(self, username):
        user_private = f'private_{username}'
        self.redis.delete(user_private)

    def add_message(self, message):
        json_message = json.dumps(message)
        self.redis.rpush('global_messages', json_message)
        self.redis.ltrim('global_messages', -RedisServer.MAX_MESSAGES, -1)
        self.redis.expire('global_messages', RedisServer.TTL)

    def get_all_messages(self):
        return self.redis.lrange('global_messages', 0, -1)

    def add_user(self, user):
        json_user = json.dumps(user)
        self.redis.zadd('global_users', {json_user: 0})
        self.redis.expire('global_users', RedisServer.TTL)

    def delete_user(self, user):
        json_user = json.dumps(user)
        self.redis.zrem('global_users', 1, json_user)

    def get_all_users(self):
        return self.redis.zrange('global_users', 0, -1)

    def get_users_list(self):
        users = self.get_all_users()
        users_list = []
        if users:
            for u in users:
                user = json.loads(u)
                username = user['username']
                users_list.append(username)

        return users_list

    def add_room(self, room_token):
        self.redis.sadd('rooms', room_token)
        self.redis.expire('rooms', RedisServer.TTL)

    def is_rooms_member(self, key):
        return self.redis.sismember('rooms', key)

    def add_search(self, username):
        self.redis.hset('search_pool', username, RedisServer.TIME_TO_SEARCH)
        self.redis.expire('search_pool', RedisServer.TTL)

    def delete_search(self, username):
        self.redis.hdel('search_pool', username)

    def get_all_search(self):
        return self.redis.hgetall('search_pool')

    def decrease_tts(self, username, value):
        self.redis.hincrby('search_pool', username, value)

    def add_player_token(self, token, username):
        self.redis.hset('player_tokens', token, username)
        self.redis.expire('player_tokens', RedisServer.TTL)

    def get_player_by_token(self, token):
        return self.redis.hget('player_tokens', token)

    def is_p_tokens_member(self, token):
        return self.redis.hexists('player_tokens', token)


class RoomManager:
    def __init__(self):
        self.length = 8
        self.max_attempts = 100
        self.ascii_chars = ''.join([string.ascii_letters, string.digits])
        self.redis = RedisServer()

    def generate_room_token(self):
        for i in range(self.max_attempts):
            random_token = ''.join(random.choices(self.ascii_chars, k=self.length))
            if not self.redis.is_rooms_member(random_token):
                self.redis.add_room(random_token)
                return random_token

        return None


class GamesManager:
    def __init__(self):
        self.length = 8
        self.max_attempts = 100
        self.ascii_chars = ''.join([string.ascii_letters, string.digits])
        self.redis = RedisServer()

    def generate_token(self, username):
        for i in range(self.max_attempts):
            token = ''.join(random.choices(self.ascii_chars, k=self.length))
            if not self.redis.is_p_tokens_member(token):
                self.redis.add_player_token(token, username)
                return token

        return None


class UsersManager:
    @staticmethod
    def add_win(username):
        url = get_users_add_win_url()
        data = {'username': username}
        requests.patch(url, data=data)

    @staticmethod
    def add_loss(username):
        url = get_users_add_loss_url()
        data = {'username': username}
        requests.patch(url, data=data)

    @staticmethod
    def add_draw(username):
        url = get_users_add_draw_url()
        data = {'username': username}
        requests.patch(url, data=data)

    @staticmethod
    def change_rating(username, rating):
        url = get_users_change_rating_url()
        data = {
            'username': username,
            'rating': rating,
        }
        requests.patch(url, data=data)

    @staticmethod
    def update_experience(charname, experience):
        url = get_users_char_experience_url()
        data = {
            'charname': charname,
            'experience': experience,
        }
        requests.patch(url, data=data)


def token_auth(func):
    def wrapper(*args, **kwargs):
        func_request = args[0]
        access = func_request.COOKIES.get('uat')
        refresh = func_request.COOKIES.get('urt')
        user = cache.get(access)
        if user:
            result = func(*args, user=user, **kwargs)
        else:
            data = {
                'access': access,
                'refresh': refresh,
            }
            cookies = func_request.COOKIES
            logger.debug(f'Cookies: {cookies}')
            users_response = try_requests(requests.post, get_users_get_user_url(), data=data, cookies=cookies)
            user = users_response.get('response').json().get('user')
            uat = users_response.get('response').json().get('uat')
            urt = users_response.get('response').json().get('urt')
            cache.set(access, user, timeout=900)
            result = func(*args, user=user, **kwargs)
            if uat:
                result.set_cookie(
                    key='uat',
                    value=access,
                    max_age=900,
                    secure=True,
                    httponly=True,
                    samesite='None',
                )
            if urt:
                result.set_cookie(
                    key='urt',
                    value=refresh,
                    max_age=3600 * 24,
                    secure=True,
                    httponly=True,
                    samesite='None',
                )
        return result
    return wrapper


def try_requests(method, url, data=None, headers=None, cookies=None,  timeout=5):
    context = {}
    response = None
    try:
        response = method(url, data=data, headers=headers, cookies=cookies, timeout=timeout)
        response.raise_for_status()
        context['status'] = response.status_code
        context['response'] = response
        return context

    except requests.exceptions.Timeout:
        # Handle timeout errors (server took too long to respond)
        context['status'] = 408
        context['errors'] = {'error': 'Request timed out. Please try again later.'}

    except requests.exceptions.ConnectionError:
        # Handle connection errors (unable to reach the server)
        context['status'] = 503
        context['errors'] = {'error': 'Connection error. Please check your network and try again.'}

    except requests.exceptions.HTTPError as e:
        if response is not None:
            context['status'] = 400
            # If a response was received, check for specific HTTP status codes
            if response.status_code == 400:
                # Parse and display field errors for invalid data
                errors = response.json().get('errors', [])
                field_errors = {field: response_messages for field, response_messages in errors}
                context['errors'] = field_errors
            else:
                context['errors'] = {'error': f'Unexpected error: {str(e)}'}
        else:
            # If no response was received, indicate server unavailability
            context['status'] = 503
            context['errors'] = {'error': 'Server is not responding, please try later.'}

    except requests.exceptions.RequestException:
        # Handle other general request errors
        context['status'] = 500
        context['errors'] = {'error': 'Unexpected error.'}

    return context

