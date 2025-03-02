import logging
import random

from game_app.game.game import Actions, Character


logger = logging.getLogger('game_server')


bot_dict = {
    'name': 'Bot',
    'owner': 'Bot',
    'strength': 5,
    'agility': 5,
    'stamina': 5,
    'endurance': 5,
}


class Bot(Character):
    def __init__(self):
        super().__init__(bot_dict)
        self.actions_dict = {
            Actions.ATTACK: 0,
            Actions.DEFEND: 0,
            Actions.FEINT: 0,
            Actions.REST: 0,
            Actions.PASS: 0,
        }
        self.status = None
        self.opponent_status = None

    def reset_actions(self):
        self.actions_dict = {
            Actions.ATTACK: 1,
            Actions.DEFEND: 1,
            Actions.FEINT: 1,
            Actions.REST: 0,
            Actions.PASS: 0,
        }

    def make_move(self) -> Actions:
        self.reset_actions()

        if self.status[1] < 20:
            return Actions.REST

        if self.status[1] < 50:
            self.actions_dict[Actions.REST] += 1

        if self.status[1] > self.opponent_status[1]:
            self.actions_dict[Actions.ATTACK] += 1

        if self.status[0] > self.opponent_status[0]:
            self.actions_dict[Actions.FEINT] += 1

        if self.status[0] < self.opponent_status[0]:
            self.actions_dict[Actions.DEFEND] += 1

        if all(action not in self.opponent_status[2] for action in ('attack', 'defend')):
            self.actions_dict[Actions.DEFEND] = 0
            self.actions_dict[Actions.FEINT] = 0

        self.get_action()
        for action in self.actions_dict.keys():
            if action not in self.available_actions:
                self.actions_dict[action] = 0

        actions_list = []
        for key, value in self.actions_dict.items():
            for i in range(value):
                actions_list.append(key)

        if len(actions_list) == 0:
            actions_list.append(Actions.PASS)

        logger.debug(f'Actions list: {actions_list}')
        return random.choice(actions_list)

    async def send_start(self, message):
        if message['p1_username'] == 'Bot':
            self.status = message['p1_status']
            self.opponent_status = message['p2_status']
        else:
            self.status = message['p2_status']
            self.opponent_status = message['p1_status']

        self.set_action(self.make_move())

    async def send_turn(self, message):
        if message['p1_username'] == 'Bot':
            self.status = message['p1_status']
            self.opponent_status = message['p2_status']
        else:
            self.status = message['p2_status']
            self.opponent_status = message['p1_status']

        self.set_action(self.make_move())

    async def send_timer(self, timer):
        pass

    async def send_game_result(self, game_result):
        pass
