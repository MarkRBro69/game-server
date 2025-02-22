import json
import logging
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer

from game_app.utils import RedisServer, ConsumerUtils, Commands, RoomManager
from game_app.game.game_searching import GameSearching


logger = logging.getLogger('game_server')


class GlobalConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.username = None
        self.user = None
        self.redis = RedisServer()
        self.room_manager = RoomManager()
        self.game_searching = None

    async def connect(self):
        self.room_group_name = 'global_lobby'
        self.username = self.scope['url_route']['kwargs']['username']
        self.user = {
            'username': self.username,
            'email': '',
        }

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        self.redis.add_user(self.user)
        self.redis.add_channel(self.username, self.channel_name)

        await self.send_messages_history()
        await self.send_all_user_update()

    async def disconnect(self, close_code):
        self.redis.delete_user(self.user)
        self.redis.delete_channel(self.username)

        await self.send_all_user_update()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        command, parsed_message, recipient = ConsumerUtils.parse_message(message)
        timestamp = datetime.now().strftime('%H:%M:%S')

        if Commands(command) == Commands.MESSAGE:
            message_to_send = {
                'type': 'message',
                'event_type': command,
                'message': parsed_message,
                'username': username,
                'timestamp': timestamp,
            }
            self.redis.add_message(message_to_send)

            await self.channel_layer.group_send(self.room_group_name, message_to_send)

        elif Commands(command) == Commands.PRIVATE:
            message_to_send = {
                'type': 'private',
                'event_type': command,
                'message': parsed_message,
                'username': username,
                'timestamp': timestamp,
            }

            recipient_channel = self.redis.get_channel(recipient)
            recipient_channel = recipient_channel.decode('utf-8')

            await self.channel_layer.send(recipient_channel, message_to_send)
            await self.channel_layer.send(self.channel_name, message_to_send)

        elif Commands(command) == Commands.INVITE:
            room_token = self.room_manager.generate_room_token()
            message_to_send = {
                'type': 'invite',
                'event_type': command,
                'message': parsed_message,
                'username': username,
                'timestamp': timestamp,
                'target_url': f'/game_lobby/{room_token}/',
            }

            recipient_channel = self.redis.get_channel(recipient)
            if recipient_channel:
                recipient_channel = recipient_channel.decode('utf-8')
                await self.channel_layer.send(recipient_channel, message_to_send)
                await self.channel_layer.send(self.channel_name, message_to_send)

        elif Commands(command) == Commands.SEARCH:
            self.game_searching = GameSearching(self.redis, self.room_manager, self.username, self)
            logger.debug(f'Search accepted for: {self.username}')

    async def message(self, event):
        event_type = event['event_type']
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'message': message,
            'username': username,
            'timestamp': timestamp,
        }))

    async def private(self, event):
        event_type = event['event_type']
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'message': f'private: {message}',
            'username': username,
            'timestamp': timestamp,
        }))

    async def invite(self, event):
        event_type = event['event_type']
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']
        target_url = event['target_url']

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'message': f'invite from {username}: {message}',
            'username': username,
            'timestamp': timestamp,
            'target_url': target_url,
        }))

    async def game_match(self, message):
        data = {
            'event_type': message['event_type'],
            'message': message['message'],
            'target_url': message['target_url'],
        }
        await self.send(text_data=json.dumps(data))

    async def new_user(self, event):
        event_type = event['event_type']
        users = event['users']

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'users': users,
        }))

    async def send_messages_history(self):
        messages = self.redis.get_all_messages()

        if messages:
            for m in messages:
                mess = json.loads(m)
                event_type = mess['event_type']
                message = mess['message']
                username = mess['username']
                timestamp = mess['timestamp']

                await self.send(text_data=json.dumps({
                    'event_type': event_type,
                    'message': message,
                    'username': username,
                    'timestamp': timestamp,
                }))

    async def send_all_user_update(self):
        users_list = self.redis.get_users_list()
        if users_list:
            message_to_send = {
                'event_type': '/new_user',
                'type': 'new_user',
                'users': users_list,
            }
            await self.channel_layer.group_send(self.room_group_name, message_to_send)
