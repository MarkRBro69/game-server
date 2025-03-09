import logging
import random

from game_app.game.actions import ActionsFactory, Action
from game_app.game.game import Character


logger = logging.getLogger('game_server')


bot_dict = {
    'name': 'Bot',
    'owner': 'Bot',
    'strength': 5,
    'agility': 5,
    'stamina': 5,
    'endurance': 5,
    'level': 1,
    'experience': 0,
}


class Bot(Character):
    def __init__(self):
        super().__init__(bot_dict)
        actions = ActionsFactory.action_classes.keys()
        self.actions_dict = {action: 0 for action in actions}
        self.status = None
        self.opponent_status = None

    def reset_actions(self):
        actions = list(ActionsFactory.action_classes.keys())
        self.actions_dict = {action: (1 if i < 3 else 0) for i, action in enumerate(actions)}

    def make_move(self) -> Action:
        self.reset_actions()

        if self.status[1] < 20:
            return ActionsFactory.create_action(action_name='pass')

        if self.status[1] < 50:
            self.actions_dict['rest'] += 1

        if self.status[1] > self.opponent_status[1]:
            self.actions_dict['attack'] += 1

        if self.status[0] > self.opponent_status[0]:
            self.actions_dict['feint'] += 1

        if self.status[0] < self.opponent_status[0]:
            self.actions_dict['defence'] += 1

        if all(action not in self.opponent_status[2] for action in ('attack', 'defend')):
            self.actions_dict['defence'] = 0
            self.actions_dict['feint'] = 0

        self.get_action()
        for action in self.actions_dict.keys():
            if action not in self.available_actions:
                self.actions_dict[action] = 0

        actions_list = []
        for key, value in self.actions_dict.items():
            for i in range(value):
                actions_list.append(key)

        if len(actions_list) == 0:
            actions_list.append('pass')

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
