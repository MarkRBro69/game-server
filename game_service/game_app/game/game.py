import asyncio
import logging

from typing import Optional

from game_app.game.actions import ActionsFactory, Action, Status
from game_app.utils import UsersManager


logger = logging.getLogger('game_server')


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
        self.current_action: Action = ActionsFactory.create_action(action_name='pass')
        self.last_action: Action = ActionsFactory.create_action(action_name='pass')
        self.ready_to_act: bool = False

    def set_action(self, action: str):
        logger.debug(f'{self.name} selected: {action}')
        self.get_action()
        if action in self.available_actions:
            action_power = 0
            if action == 'attack':
                action_power = self.damage
            elif action == 'rest':
                action_power = self.aer

            self.current_action = ActionsFactory.create_action(action_name=action,
                                                               energy_cost=self.epa,
                                                               action_power=action_power)
            self.ready_to_act = True

    def get_action(self) -> Action:
        self.last_action = self.current_action
        self.current_action = ActionsFactory.create_action(action_name='pass')
        self.ready_to_act = False
        return self.last_action

    def get_last_action(self) -> str:
        return self.last_action.action_name

    def get_name(self) -> str:
        return self.name

    def apply_status(self, stat: Status) -> None:
        self.health += stat.status.get('health')
        if self.health <= 0:
            self.is_dead = True

        self.energy += stat.status.get('energy')
        if self.energy < 0:
            self.energy = 0
        elif self.energy > self.MAX_ENERGY:
            self.energy = self.MAX_ENERGY
            
        self.skip_turn = stat.status.get('skip')

    def get_actions(self) -> list:
        self.available_actions = set()
        if self.is_dead:
            return []

        if self.skip_turn:
            self.available_actions = {'pass'}

        else:
            self.available_actions = set(ActionsFactory.action_classes.keys())
            self.available_actions.remove('pass')
            if self.energy < self.epa:
                self.available_actions.remove('attack')
                self.available_actions.remove('defence')

        return list(self.available_actions)

    def turn(self, stat: Status):
        self.apply_status(stat)
        self.energy += self.ber

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
            character.skip_turn = False

        p1_action = self.characters[1].get_action()
        p2_action = self.characters[2].get_action()

        status1, status2 = Action.resolve_actions(p1_action, p2_action)

        self.characters[1].turn(status1)
        self.characters[2].turn(status2)

        game_message = (
            f'Turn: {self.turn_number}:\n'
            f'{self.characters[1].get_name()}: {p1_action.action_name}\n'
            f'{self.characters[2].get_name()}: {p2_action.action_name}'
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
