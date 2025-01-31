import asyncio
import logging

from enum import Enum
from typing import Optional

from game_service.utils import UsersManager


logger = logging.getLogger('game_server')


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
        logger.debug(f'action 1: {action1}, action 2: {action2}')

        if (action1, action2) in cls.INTERACTIONS:
            return cls.INTERACTIONS[(action1, action2)]
        elif (action2, action1) in cls.INTERACTIONS:
            return tuple(cls.INTERACTIONS[(action2, action1)][3:] + cls.INTERACTIONS[(action2, action1)][:3])
        else:
            raise ValueError('Interaction is not allowed')


class Player:
    def __init__(self, username: str) -> None:
        self.username: str = username
        self.health: int = 100
        self.energy: int = 100
        self.skip_turn: bool = False
        self.is_dead: bool = False

        self.available_actions: set = set()
        self.current_action: Actions = Actions.PASS
        self.last_action: Actions = Actions.PASS
        self.ready_to_act: bool = False

    def set_action(self, action: Actions):
        logger.debug(f'{self.username} selected: {action}')

        self.current_action = Actions(action)
        self.ready_to_act = True

    def get_action(self) -> Actions:
        self.last_action = self.current_action
        self.current_action = Actions.PASS
        self.ready_to_act = False
        return self.last_action

    def get_last_action(self) -> str:
        return self.last_action.value

    def get_username(self) -> str:
        return self.username

    def change_health(self, amount: int) -> None:
        self.health += amount

        if self.health <= 0:
            self.is_dead = True

    def change_energy(self, amount: int) -> None:
        self.energy += amount

        if self.energy > 100:
            self.energy = 100

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
            if self.energy < Interactions.ENERGY_COST:
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

    def __init__(self) -> None:
        self.players: dict[int, Optional[Player]] = {1: None, 2: None}
        self.turn_number = 0
        self.game_started: bool = False

        self.usernames_dict: dict = {}
        self.observers: list = []

    async def set_player(self, player: Player) -> None:
        logger.debug(f'Player {player.get_username()} connected')

        if self.players[1] is None:
            self.players[1] = player
        else:
            self.players[2] = player

        self.usernames_dict[player.get_username()] = player

        if all(self.players.values()) and not self.game_started:
            await self.send_start()
            self.game_started = True
            asyncio.create_task(self.start())

    def get_player_by_username(self, username):
        return self.usernames_dict[username]

    def get_status(self):
        return self.players[1].get_status(), self.players[2].get_status()

    def turn_ready(self) -> bool:
        return all(player.ready_to_act for player in self.players.values())

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
                #  --add to db
                await self.send_game_result(game_result)
                break

    def turn(self) -> str:
        for player in self.players.values():
            player.change_skip(False)

        p1_action = self.players[1].get_action()
        p2_action = self.players[2].get_action()

        h1_change, e1_change, p1_skip, h2_change, e2_change, p2_skip = (
            Interactions.parse_actions(p1_action, p2_action)
        )

        self.players[1].turn(h1_change, e1_change, p1_skip)
        self.players[2].turn(h2_change, e2_change, p2_skip)

        game_message = (
            f'Turn: {self.turn_number}:\n'
            f'{self.players[1].get_username()}: {p1_action.value}\n'
            f'{self.players[2].get_username()}: {p2_action.value}'
        )

        return game_message

    def check_end_condition(self, turn_number: int) -> str:
        p1_username = self.players[1].get_username()
        p2_username = self.players[2].get_username()

        if self.players[1].is_dead and self.players[2].is_dead:
            UsersManager.add_draw(p1_username)
            UsersManager.add_draw(p2_username)
            return 'draw'
        if self.players[1].is_dead:
            UsersManager.add_loss(p1_username)
            UsersManager.change_rating(p1_username, -self.RATING_PER_GAME)

            UsersManager.add_win(p2_username)
            UsersManager.change_rating(p2_username, self.RATING_PER_GAME)
            return 'p2 win'
        if self.players[2].is_dead:
            UsersManager.add_win(p1_username)
            UsersManager.change_rating(p1_username, self.RATING_PER_GAME)

            UsersManager.add_loss(p2_username)
            UsersManager.change_rating(p2_username, -self.RATING_PER_GAME)
            return 'p1 win'
        if turn_number == Game.MAX_TURNS - 1:
            UsersManager.add_draw(p1_username)
            UsersManager.add_draw(p2_username)
            return 'draw'
        return ''

    def set_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    async def send_start(self) -> None:
        message = {
            'message': 'game started',
            'p1_username': self.players[1].get_username(),
            'p1_status': self.players[1].get_status(),
            'p2_username': self.players[2].get_username(),
            'p2_status': self.players[2].get_status(),
        }

        for observer in self.observers:
            await observer.send_start(message)

    async def send_turn(self, game_message) -> None:
        message = {
            'message': game_message,
            'p1_username': self.players[1].get_username(),
            'p1_status': self.players[1].get_status(),
            'p1_action': self.players[1].get_last_action(),
            'p2_username': self.players[2].get_username(),
            'p2_status': self.players[2].get_status(),
            'p2_action': self.players[2].get_last_action(),
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
