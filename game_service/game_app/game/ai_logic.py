import random

from game_app.game.game import Actions


class Bot:
    def __init__(self):
        self.actions_dict = {
            Actions.ATTACK: 0,
            Actions.DEFEND: 0,
            Actions.FEINT: 0,
            Actions.REST: 0,
            Actions.PASS: 0,
        }

    def reset_actions(self):
        self.actions_dict = {
            Actions.ATTACK: 1,
            Actions.DEFEND: 1,
            Actions.FEINT: 1,
            Actions.REST: 0,
            Actions.PASS: 0,
        }

    def make_move(self, bot_player, human_player) -> Actions:
        self.reset_actions()

        if bot_player.get('energy') < 20:
            return Actions.REST

        if bot_player.get('energy') < 50:
            self.actions_dict[Actions.REST] += 1

        if bot_player.get('energy') > human_player.get('energy'):
            self.actions_dict[Actions.ATTACK] += 1

        if bot_player.get('hp') > human_player.get('hp'):
            self.actions_dict[Actions.FEINT] += 1

        if bot_player.get('hp') < human_player.get('hp'):
            self.actions_dict[Actions.DEFEND] += 1

        actions_list = []
        for key, value in self.actions_dict:
            for i in range(value):
                actions_list.append(key)

        return random.choice(actions_list)