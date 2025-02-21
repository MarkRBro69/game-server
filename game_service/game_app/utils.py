import json
import random
import string
from enum import Enum

import redis
import requests
from django.conf import settings

from game_service.microservices.users_api import (
    get_users_add_win_url,
    get_users_add_loss_url,
    get_users_add_draw_url,
    get_users_change_rating_url
)


class Commands(Enum):
    INVITE = '/invite'
    PRIVATE = '/private'
    MESSAGE = '/message'

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

    def is_rooms_member(self, key, value):
        return self.redis.sismember(key, value)

    def add_search(self, username):
        self.redis.sadd('search_pool', username)
        self.redis.expire('search_pool', RedisServer.TTL)

    def delete_search(self, username):
        self.redis.srem('search_pool', username)


class RoomManager:
    def __init__(self):
        self.length = 8
        self.max_attempts = 100
        self.ascii_chars = ''.join([string.ascii_letters, string.digits])
        self.redis = RedisServer()

    def generate_room_token(self):
        for i in range(self.max_attempts):
            random_token = ''.join(random.choices(self.ascii_chars, k=self.length))
            if not self.redis.is_rooms_member('rooms', random_token):
                self.redis.add_room(random_token)
                return random_token

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
