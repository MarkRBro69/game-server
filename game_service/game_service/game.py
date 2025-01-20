import random
from enum import Enum


class Actions(Enum):
    ATTACK = 'attack'
    DEFEND = 'defend'
    FEINT = 'feint'
    REST = 'rest'
    PASS = 'pass'


class Interactions:
    ATTACK_DAMAGE = 10
    ENERGY_COST = 20
    FAIL_MULTIPLY = 2
    ENERGY_PER_TURN = 10

    INTERACTIONS = {
        (Actions.ATTACK, Actions.ATTACK): (-ATTACK_DAMAGE, -ENERGY_COST, False, -ATTACK_DAMAGE, -ENERGY_COST, False),
        (Actions.ATTACK, Actions.DEFEND): (0, -ENERGY_COST * FAIL_MULTIPLY, True, 0, -ENERGY_COST, False),
        (Actions.ATTACK, Actions.FEINT): (0, -ENERGY_COST, False, -ATTACK_DAMAGE, 0, False),
        (Actions.ATTACK, Actions.REST): (0, -ENERGY_COST, False, -ATTACK_DAMAGE, ENERGY_COST, False),
        (Actions.ATTACK, Actions.PASS): (0, -ENERGY_COST, False, -ATTACK_DAMAGE, 0, False),
        (Actions.DEFEND, Actions.DEFEND): (0, 0, False, 0, 0, False),
        (Actions.DEFEND, Actions.FEINT): (0, -ENERGY_COST * FAIL_MULTIPLY, True, 0, 0, False),
        (Actions.DEFEND, Actions.REST): (0, 0, False, 0, ENERGY_COST, False),
        (Actions.DEFEND, Actions.PASS): (0, 0, False, 0, 0, False),
        (Actions.FEINT, Actions.FEINT): (0, 0, False, 0, 0, False),
        (Actions.FEINT, Actions.REST): (0, 0, False, 0, ENERGY_COST, False),
        (Actions.FEINT, Actions.PASS): (0, 0, False, 0, 0, False),
        (Actions.REST, Actions.REST): (0, ENERGY_COST, False, 0, ENERGY_COST, False),
        (Actions.REST, Actions.PASS): (0, ENERGY_COST, False, 0, 0, False),
        (Actions.PASS, Actions.PASS): (0, 0, False, 0, 0, False),
    }

    @classmethod
    def parse_actions(cls, action1, action2):
        if (action1, action2) in cls.INTERACTIONS:
            return cls.INTERACTIONS[(action1, action2)]
        elif (action2, action1) in cls.INTERACTIONS:
            return tuple(cls.INTERACTIONS[(action2, action1)][3:] + cls.INTERACTIONS[(action2, action1)][:3])
        else:
            raise ValueError('Interaction is not allowed')


class Game:
    def __init__(self) -> None:
        self.player1 = Player()
        self.player2 = Player()

        self.player1_is_ready = False
        self.player2_is_ready = False

        self.player1_action = None
        self.player2_action = None

        self.player1_state = None
        self.player2_state = None

    def set_player1_name(self, username):
        self.player1.set_username(username)
        return self.game_init()

    def set_player2_name(self, username):
        self.player2.set_username(username)
        return self.game_init()

    def set_player1_is_ready(self):
        self.player1_is_ready = True
        return self.start()

    def set_player2_is_ready(self):
        self.player2_is_ready = True
        return self.start()

    def set_player1_action(self, action):
        parsed_action = Actions(action)
        if parsed_action in self.player1.available_actions:
            self.player1_action = parsed_action
        else:
            self.player1_action = Actions.PASS

        return self.turn()

    def set_player2_action(self, action):
        parsed_action = Actions(action)
        if parsed_action in self.player2.available_actions:
            self.player2_action = parsed_action
        else:
            self.player2_action = Actions.PASS

        return self.turn()

    def game_init(self):
        action_flag = False
        if self.player1.username is None or self.player2.username is None:
            return None, None, action_flag

        action_flag = True
        return action_flag

    def start(self):
        action_flag = False
        if not self.player1_is_ready or not self.player2_is_ready:
            return None, None, action_flag

        self.player1_state = self.player1.get_state()
        self.player2_state = self.player2.get_state()
        action_flag = True

        return self.player1_state, self.player2_state, action_flag

    def turn(self):
        action_flag = False
        if self.player1_action is None or self.player2_action is None:
            return None, None, action_flag

        h1_change, e1_change, p1_skip, h2_change, e2_change, p2_skip = (
            Interactions.parse_actions(self.player1_action, self.player2_action)
        )

        self.player1_action = None
        self.player2_action = None

        self.player1.change_health(h1_change)
        self.player1.change_energy(e1_change)
        self.player1.change_skip(p1_skip)

        self.player2.change_health(h2_change)
        self.player2.change_energy(e2_change)
        self.player2.change_skip(p2_skip)

        self.player1_state = self.player1.get_state()
        self.player2_state = self.player2.get_state()

        action_flag = True

        if self.player1_state is None:
            if self.player2_state is None:
                return 'draw', None, action_flag

            return f'{self.player2.username} win', None, action_flag

        if self.player2_state is None:
            return f'{self.player1.username} win', None, action_flag

        return self.player1_state, self.player2_state, action_flag


class Player:
    def __init__(self) -> None:
        self.username = None
        self.health = 100
        self.energy = 100
        self.skip = False
        self.available_actions = {}

    def set_username(self, username: str):
        self.username = username

    def change_health(self, amount):
        self.health += amount

    def change_energy(self, amount):
        self.energy += amount

        if self.energy > 100:
            self.energy = 100

        if self.energy < 0:
            self.energy = 0

    def change_skip(self, skip):
        self.skip = skip

    def get_state(self):
        if self.health <= 0:
            return None

        if self.skip:
            self.available_actions = {Actions.PASS}
            self.skip = False

        else:
            self.available_actions = set(Actions)
            self.available_actions.remove(Actions.PASS)
            if self.energy < Interactions.ENERGY_COST:
                self.available_actions.remove(Actions.ATTACK)
                self.available_actions.remove(Actions.DEFEND)

        return self.health, self.energy, self.available_actions


class GameHandler:
    games = {}

    @classmethod
    def add_game(cls, room_token: str) -> (Game, bool):
        firs_player = False
        room_game = cls.games.get(room_token)
        if not room_game:
            firs_player = True
            room_game = Game()
            cls.games[room_token] = room_game

        return room_game, firs_player

    @classmethod
    def get_game(cls, room_token: str) -> Game:
        return cls.games[room_token]


if __name__ == '__main__':
    game = Game()
    action_flag = False

    p1 = game.player1
    action_flag = game.set_player1_name('mark')

    p2 = game.player2
    action_flag = game.set_player2_name('philip')

    if action_flag:
        print('game initialized')
    action_flag = False

    state_p1, state_p2, action_flag = game.set_player1_is_ready()
    state_p1, state_p2, action_flag = game.set_player2_is_ready()

    if action_flag:
        print('Game started')
        print(f'{p1.username}: health: {state_p1[0]}, energy: {state_p1[1]}\n'
              f'available actions: {state_p1[2]}')
        print(f'{p2.username}: health: {state_p2[0]}, energy: {state_p2[1]}\n'
              f'available actions: {state_p2[2]}')

        while not isinstance(state_p1, str):
            if state_p1[2]:
                action1 = random.choice(list(state_p1[2]))
            else:
                action1 = Actions.PASS

            if state_p2[2]:
                action2 = random.choice(list(state_p2[2]))
            else:
                action2 = Actions.PASS

            state_p1, state_p2, action_flag = game.set_player1_action(action1)
            state_p1, state_p2, action_flag = game.set_player2_action(action2)

            print(f'{p1.username} action: {action1}')
            print(f'{p2.username} action: {action2}')

            if isinstance(state_p1, str):
                print(state_p1)
            else:
                print(f'{p1.username}: health: {state_p1[0]}, energy: {state_p1[1]}\n'
                      f'available actions: {state_p1[2]}')
                print(f'{p2.username}: health: {state_p2[0]}, energy: {state_p2[1]}\n'
                      f'available actions: {state_p2[2]}')
