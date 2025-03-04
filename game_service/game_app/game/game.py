import asyncio
import logging

from enum import Enum
from typing import Optional

from game_app.utils import UsersManager


logger = logging.getLogger('game_server')


class Actions(Enum):
    ATTACK = 'attack'
    DEFEND = 'defend'
    FEINT = 'feint'
    REST = 'rest'
    PASS = 'pass'


class Interactions:
    MULTIPLY = 2

    INTERACTIONS = {
        (Actions.ATTACK, Actions.ATTACK): (-1, -1, False, -1, -1, False),
        (Actions.ATTACK, Actions.DEFEND): (0, -1 * MULTIPLY, True, 0, -1, False),
        (Actions.ATTACK, Actions.FEINT): (0, -1, False, -1, 0, False),
        (Actions.ATTACK, Actions.REST): (0, -1, False, -1, 1, False),
        (Actions.ATTACK, Actions.PASS): (0, -1, False, -1, 0, False),

        (Actions.DEFEND, Actions.DEFEND): (0, 0, False, 0, 0, False),
        (Actions.DEFEND, Actions.FEINT): (0, -1 * MULTIPLY, True, 0, 0, False),
        (Actions.DEFEND, Actions.REST): (0, 0, False, 0, 1, False),
        (Actions.DEFEND, Actions.PASS): (0, 0, False, 0, 0, False),

        (Actions.FEINT, Actions.FEINT): (0, 0, False, 0, 0, False),
        (Actions.FEINT, Actions.REST): (0, 0, False, 0, 1, False),
        (Actions.FEINT, Actions.PASS): (0, 0, False, 0, 0, False),

        (Actions.REST, Actions.REST): (0, 1, False, 0, 1, False),
        (Actions.REST, Actions.PASS): (0, 1, False, 0, 0, False),

        (Actions.PASS, Actions.PASS): (0, 0, False, 0, 0, False),
    }

    @classmethod
    def parse_actions(cls, action1, action2):
        logger.debug(f'action 1: {action1}, action 2: {action2}')

        if (action1, action2) in cls.INTERACTIONS:
            return cls.INTERACTIONS[(action1, action2)]
        elif (action2, action1) in cls.INTERACTIONS:
            return tuple(cls.INTERACTIONS[(action2, action1)][3:] + cls.INTERACTIONS[(action2, action1)][:3])
        else:
            raise ValueError('Interaction is not allowed')


class Character:
    hp_per_endurance = 20
    en_per_stamina = 20
    dmg_per_strength = 4
    be_per_stamina = 2
    ae_per_stamina = 8

    def __init__(self, character: dict) -> None:
        self.MAX_ENERGY: int = character.get('stamina') * Character.en_per_stamina
        self.OWNER_USERNAME: str = character.get('owner')

        self.name: str = character.get('name')
        self.health: int = character.get('endurance') * Character.hp_per_endurance
        self.energy: int = self.MAX_ENERGY
        self.damage: int = character.get('strength') * Character.dmg_per_strength
        self.epa: int = 100 // character.get('agility')  # Energy per action
        self.ber: int = character.get('stamina') * Character.be_per_stamina  # Base energy recharge
        self.aer: int = character.get('stamina') * Character.ae_per_stamina  # Active energy recharge

        self.level: int = character.get('level')
        self.experience: int = character.get('experience')

        self.skip_turn: bool = False
        self.is_dead: bool = False

        self.available_actions: set = set()
        self.current_action: Actions = Actions.PASS
        self.last_action: Actions = Actions.PASS
        self.ready_to_act: bool = False

    def set_action(self, action: Actions):
        logger.debug(f'{self.name} selected: {action}, Actions: {Actions(action)}')
        self.get_action()
        if Actions(action) in self.available_actions:
            self.current_action = Actions(action)
            self.ready_to_act = True

    def get_action(self) -> Actions:
        self.last_action = self.current_action
        self.current_action = Actions.PASS
        self.ready_to_act = False
        return self.last_action

    def get_last_action(self) -> str:
        return self.last_action.value

    def get_name(self) -> str:
        return self.name

    def change_health(self, amount: int) -> None:
        self.health += amount

        if self.health <= 0:
            self.is_dead = True

    def change_energy(self, amount: int) -> None:
        self.energy += amount

        if self.energy > self.MAX_ENERGY:
            self.energy = self.MAX_ENERGY

        if self.energy < 0:
            self.energy = 0

    def change_skip(self, to_skip: bool) -> None:
        self.skip_turn = to_skip

    def get_actions(self) -> list:
        self.available_actions = set()
        if self.is_dead:
            return []

        if self.skip_turn:
            self.available_actions = {Actions.PASS}

        else:
            self.available_actions = set(Actions)
            self.available_actions.remove(Actions.PASS)
            if self.energy < self.epa:
                self.available_actions.remove(Actions.ATTACK)
                self.available_actions.remove(Actions.DEFEND)

        return [action.value for action in self.available_actions]

    def turn(self, health_amount: int, energy_amount: int, to_skip: bool):
        self.change_health(health_amount)
        self.change_energy(energy_amount)
        self.change_skip(to_skip)

    def get_status(self) -> (int, int, set, bool):
        return self.health, self.energy, self.get_actions(), self.is_dead


class Game:
    MAX_TURNS = 100
    TURN_TIME = 30
    RATING_PER_GAME = 25
    EXP_GAIN = 10

    def __init__(self) -> None:
        self.characters: dict[int, Optional[Character]] = {1: None, 2: None}
        self.turn_number = 0
        self.game_started: bool = False

        self.names_dict: dict = {}
        self.observers: list = []

        self.current_game_task = None

    def calc_experience(self, target_character_level: int, enemy_character_level: int) -> int:
        exp_coef = enemy_character_level / target_character_level
        exp_gain = self.EXP_GAIN * exp_coef
        return int(exp_gain)

    async def set_character(self, character: Character) -> None:
        logger.debug(f'PLayer {character.OWNER_USERNAME} connected with: Character {character.get_name()}')

        if self.characters[1] is None:
            self.characters[1] = character
        else:
            self.characters[2] = character

        self.names_dict[character.get_name()] = character

        if all(self.characters.values()) and not self.game_started:
            await self.send_start()
            self.game_started = True
            asyncio.create_task(self.start())

    def get_character_by_name(self, name):
        return self.names_dict[name]

    def get_status(self):
        return self.characters[1].get_status(), self.characters[2].get_status()

    def turn_ready(self) -> bool:
        return all(player.ready_to_act for player in self.characters.values())

    async def start(self) -> None:
        for i in range(Game.MAX_TURNS):
            self.turn_number += 1
            duration = Game.TURN_TIME
            while duration > 0:
                if self.turn_ready():
                    game_message = self.turn()
                    await self.send_turn(game_message)
                    break

                await asyncio.sleep(1)
                duration -= 1
                await self.send_timer(duration)

            if duration == 0:
                game_message = self.turn()
                await self.send_turn(game_message)

            game_result = self.check_end_condition(i)
            if game_result != '':
                if self.current_game_task is not None:
                    self.current_game_task.cancel()
                    try:
                        await self.current_game_task
                        self.current_game_task = None
                    except asyncio.CancelledError:
                        pass

                await self.send_game_result(game_result)
                break

    def turn(self) -> str:
        for character in self.characters.values():
            character.change_skip(False)

        p1_action = self.characters[1].get_action()
        p2_action = self.characters[2].get_action()

        h1_change, e1_change, p1_skip, h2_change, e2_change, p2_skip = (
            Interactions.parse_actions(p1_action, p2_action)
        )

        h1_change *= self.characters[2].damage
        if e1_change < 0:
            e1_change = e1_change * self.characters[1].epa + self.characters[1].ber
        else:
            e1_change = e1_change * self.characters[1].aer + self.characters[1].ber

        h2_change *= self.characters[1].damage
        if e2_change < 0:
            e2_change = e2_change * self.characters[2].epa + self.characters[2].ber
        else:
            e2_change = e2_change * self.characters[2].aer + self.characters[2].ber

        self.characters[1].turn(h1_change, e1_change, p1_skip)
        self.characters[2].turn(h2_change, e2_change, p2_skip)

        game_message = (
            f'Turn: {self.turn_number}:\n'
            f'{self.characters[1].get_name()}: {p1_action.value}\n'
            f'{self.characters[2].get_name()}: {p2_action.value}'
        )

        return game_message

    def check_end_condition(self, turn_number: int) -> str:
        c1_name = self.characters[1].OWNER_USERNAME
        c2_name = self.characters[2].OWNER_USERNAME

        if self.characters[1].is_dead and self.characters[2].is_dead:
            UsersManager.add_draw(c1_name)
            UsersManager.add_draw(c2_name)
            return 'draw'

        if self.characters[1].is_dead:
            UsersManager.add_loss(c1_name)
            UsersManager.change_rating(c1_name, -self.RATING_PER_GAME)

            UsersManager.add_win(c2_name)
            UsersManager.change_rating(c2_name, self.RATING_PER_GAME)

            experience_to_gain = self.calc_experience(self.characters[2].level, self.characters[1].level)
            UsersManager.update_experience(self.characters[2].get_name(), experience_to_gain)

            return f'{c2_name} win'

        if self.characters[2].is_dead:
            UsersManager.add_win(c1_name)
            UsersManager.change_rating(c1_name, self.RATING_PER_GAME)

            UsersManager.add_loss(c2_name)
            UsersManager.change_rating(c2_name, -self.RATING_PER_GAME)

            experience_to_gain = self.calc_experience(self.characters[1].level, self.characters[2].level)
            UsersManager.update_experience(self.characters[1].get_name(), experience_to_gain)

            return f'{c1_name} win'

        if turn_number == Game.MAX_TURNS - 1:
            UsersManager.add_draw(c1_name)
            UsersManager.add_draw(c2_name)
            return 'draw'
        return ''

    def set_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    async def send_start(self) -> None:
        message = {
            'message': 'game started',
            'p1_username': self.characters[1].get_name(),
            'p1_status': self.characters[1].get_status(),
            'p2_username': self.characters[2].get_name(),
            'p2_status': self.characters[2].get_status(),
        }

        for observer in self.observers:
            await observer.send_start(message)

    async def send_turn(self, game_message) -> None:
        message = {
            'message': game_message,
            'p1_username': self.characters[1].get_name(),
            'p1_status': self.characters[1].get_status(),
            'p1_action': self.characters[1].get_last_action(),
            'p2_username': self.characters[2].get_name(),
            'p2_status': self.characters[2].get_status(),
            'p2_action': self.characters[2].get_last_action(),
        }

        for observer in self.observers:
            await observer.send_turn(message)

    async def send_timer(self, timer: int) -> None:
        message = {
            'message': 'timer update',
            'timer': timer,
        }

        for observer in self.observers:
            await observer.send_timer(message)

    async def send_game_result(self, game_result):
        message = {
            'message': f'game ended: {game_result}',
        }

        for observer in self.observers:
            await observer.send_game_result(message)


class GameHandler:
    games = {}

    @classmethod
    def get_or_add(cls, room_token: str) -> Game:
        room_game = cls.games.get(room_token)
        if not room_game:
            room_game = Game()
            cls.games[room_token] = room_game

        return room_game
