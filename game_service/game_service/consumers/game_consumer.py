import json
from channels.generic.websocket import AsyncWebsocketConsumer

from game_service.game import GameHandler


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_token = None
        self.room_group_name = None
        self.username = None
        self.user = None
        self.you = None
        self.p1_state = None
        self.p2_state = None

    async def connect(self):
        self.room_token = self.scope['url_route']['kwargs']['room_token']
        self.room_group_name = self.room_token

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

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_connect',
                'message': f'Player {self.username} connected: {self.channel_name}',
            }
        )

        game, first_player = GameHandler.add_game(self.room_token)
        if first_player:
            self.you = 1
            action_flag = game.set_player1_name(self.username)
        else:
            self.you = 2
            action_flag = game.set_player2_name(self.username)

        if action_flag:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_init',
                    'message': 'game initialization',
                    'p1_available_actions': 'ready',
                    'p2_available_actions': 'ready',
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        choice = data['choice']

        if choice == 'ready':
            game = GameHandler.get_game(self.room_token)
            if self.you == 1:
                self.p1_state, self.p2_state, action_flag = game.set_player1_is_ready()
            else:
                self.p1_state, self.p2_state, action_flag = game.set_player2_is_ready()

            if action_flag:
                p1_available_actions = ''
                if self.p1_state[2]:
                    p1_available_actions = ','.join(action.value for action in self.p1_state[2])

                p2_available_actions = ''
                if self.p2_state[2]:
                    p2_available_actions = ','.join(action.value for action in self.p2_state[2])

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_start',
                        'message': 'game started',
                        'p1_username': game.player1.username,
                        'p1_health': self.p1_state[0],
                        'p1_energy': self.p1_state[1],
                        'p1_available_actions': p1_available_actions,
                        'p2_username': game.player2.username,
                        'p2_health': self.p2_state[0],
                        'p2_energy': self.p2_state[1],
                        'p2_available_actions': p2_available_actions,
                    }
                )

        else:
            game = GameHandler.get_game(self.room_token)
            if self.you == 1:
                self.p1_state, self.p2_state, action_flag = game.set_player1_action(choice)
            else:
                self.p1_state, self.p2_state, action_flag = game.set_player2_action(choice)

            if action_flag:
                p1_available_actions = ''
                if self.p1_state[2]:
                    p1_available_actions = ','.join(action.value for action in self.p1_state[2])

                p2_available_actions = ''
                if self.p2_state[2]:
                    p2_available_actions = ','.join(action.value for action in self.p2_state[2])

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_turn',
                        'message': 'game turn',
                        'p1_username': game.player1.username,
                        'p1_health': self.p1_state[0],
                        'p1_energy': self.p1_state[1],
                        'p1_available_actions': p1_available_actions,
                        'p2_username': game.player2.username,
                        'p2_health': self.p2_state[0],
                        'p2_energy': self.p2_state[1],
                        'p2_available_actions': p2_available_actions,
                    }
                )

    async def game_init(self, event):
        data = {
            'message': event['message'],
            'p1_available_actions': event['p1_available_actions'],
            'p2_available_actions': event['p2_available_actions'],
        }
        await self.send(text_data=json.dumps(data))

    async def game_start(self, event):
        data = {
            'message': event['message'],
            'p1_username': event['p1_username'],
            'p1_health': event['p1_health'],
            'p1_energy': event['p1_energy'],
            'p1_available_actions': event['p1_available_actions'],
            'p2_username': event['p2_username'],
            'p2_health': event['p2_health'],
            'p2_energy': event['p2_energy'],
            'p2_available_actions': event['p2_available_actions'],
        }
        await self.send(text_data=json.dumps(data))

    async def game_turn(self, event):
        data = {
            'message': event['message'],
            'p1_username': event['p1_username'],
            'p1_health': event['p1_health'],
            'p1_energy': event['p1_energy'],
            'p1_available_actions': event['p1_available_actions'],
            'p2_username': event['p2_username'],
            'p2_health': event['p2_health'],
            'p2_energy': event['p2_energy'],
            'p2_available_actions': event['p2_available_actions'],
        }
        await self.send(text_data=json.dumps(data))

    async def player_ready(self, event):
        data = {
            'message': event['message']
        }
        await self.send(text_data=json.dumps(data))

    async def player_connect(self, event):
        data = {
            'message': event['message']
        }
        await self.send(text_data=json.dumps(data))

