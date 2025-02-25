import json
import logging
import requests

from channels.generic.websocket import AsyncWebsocketConsumer

from game_app.game.game import GameHandler, Character


logger = logging.getLogger('game_server')


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_token = None
        self.room_group_name = None
        self.username = None
        self.user = None
        self.character = None
        self.character_name = None

    async def connect(self):
        self.room_token = self.scope['url_route']['kwargs']['room_token']
        self.room_group_name = self.room_token

        self.username = self.scope['url_route']['kwargs']['username']
        self.user = {
            'username': self.username,
            'email': '',
        }
        self.character_name = self.scope['url_route']['kwargs']['char_name']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_connect',
                'message': f'{self.username} connected to game',
            }
        )

        headers = dict(self.scope["headers"])
        logger.debug(headers)
        cookie_value = None
        for key, value in headers.items():
            if key == b"cookie":
                cookies_dict = dict(item.split("=") for item in value.decode().split("; "))
                cookie_value = cookies_dict.get("uat", "Not Found")
        logger.debug(cookie_value)

        game = GameHandler.get_or_add(self.room_token)
        game.set_observer(self)

        if game.game_started:
            self.character = game.get_character_by_name(self.username)
            p1_status, p2_status = game.get_status()
            data_dict = {
                'message_type': 'game started',
                'message': 'reconnect',
                'p1_username': game.characters[1].get_name(),
                'p1_status': p1_status,
                'p2_username': game.characters[2].get_name(),
                'p2_status': p2_status,
            }
            data = json.dumps(data_dict)
            await self.send(text_data=data)
        else:
            self.character = requests.get()
            await game.set_character(self.character)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        game = GameHandler.get_or_add(self.room_token)
        game.remove_observer(self)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        choice = data['choice']
        logger.debug(f'Player {self.character.get_name()}: action: {choice}')

        self.character.set_action(choice)

    async def player_connect(self, event):
        data = {
            'message_type': 'player connect',
            'message': event['message']
        }
        await self.send(text_data=json.dumps(data))

    async def send_start(self, message):
        data = {
            'message_type': 'game started',
            'message': message['message'],
            'p1_username': message['p1_username'],
            'p1_status': message['p1_status'],
            'p2_username': message['p2_username'],
            'p2_status': message['p2_status'],
        }
        await self.send(text_data=json.dumps(data))

    async def send_turn(self, message):
        data = {
            'message_type': 'turn',
            'message': message['message'],
            'p1_username': message['p1_username'],
            'p1_status': message['p1_status'],
            'p1_action': message['p1_action'],
            'p2_username': message['p2_username'],
            'p2_status': message['p2_status'],
            'p2_action': message['p2_action'],
        }
        await self.send(text_data=json.dumps(data))

    async def send_timer(self, message):
        data = {
            'message_type': 'timer',
            'message': message['message'],
            'timer': message['timer'],
        }
        await self.send(text_data=json.dumps(data))

    async def send_game_result(self, message):
        data = {
            'message_type': 'game result',
            'message': message['message'],
        }
        await self.send(text_data=json.dumps(data))
