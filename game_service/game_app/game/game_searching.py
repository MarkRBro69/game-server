import asyncio
import logging

from game_app.game.ai_logic import Bot
from game_app.game.game import GameHandler

logger = logging.getLogger('game_server')


class GameSearching:
    _instance = None

    TIMEOUT = 5
    LOOP_LIMIT = 100
    SHOULD_RESTART = False
    LOOP_TASK = None
    OBSERVERS = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, redis, room_manager, username, observer):
        self.redis = redis
        self.room_manager = room_manager

        logger.debug(f'Game searching init: {username}, {observer}, {GameSearching.LOOP_TASK}')

        GameSearching.OBSERVERS[username] = observer
        self.redis.add_search(username)

        if GameSearching.LOOP_TASK is None:
            GameSearching.LOOP_TASK = asyncio.create_task(self.check_loop())
        else:
            GameSearching.SHOULD_RESTART = True

    async def check_loop(self):
        for i in range(GameSearching.LOOP_LIMIT):
            logger.debug(f'Check loop running: {i}')
            if GameSearching.SHOULD_RESTART:
                GameSearching.SHOULD_RESTART = False
                await self.restart_loop()
                return

            try:
                await self.check_match()
                await asyncio.sleep(GameSearching.TIMEOUT)
            except asyncio.CancelledError:
                logger.debug("Loop was cancelled.")
                return

    async def restart_loop(self):
        if GameSearching.LOOP_TASK:
            GameSearching.LOOP_TASK.cancel()

            GameSearching.LOOP_TASK = asyncio.create_task(self.check_loop())

    @classmethod
    async def end_loop(cls):
        logger.debug(f'LOOP TASK: {cls.LOOP_TASK}')
        if cls.LOOP_TASK is not None:
            cls.LOOP_TASK.cancel()

            cls.LOOP_TASK = None

    async def check_match(self):
        searching_users = self.redis.get_all_search()

        logger.debug(f'Checking match, searching players:'
                     f'{searching_users}')

        if len(searching_users) == 0:
            logger.debug('Run end_loop')
            await self.end_loop()

        match_dict = {}
        for username, time_to_search in searching_users.items():
            username = username.decode('utf-8')
            time_to_search = time_to_search.decode('utf-8')

            match_dict[username] = time_to_search

            if len(match_dict) == 2:
                await self.send_invites(match_dict)
                match_dict = {}

        if len(match_dict) == 1:
            username, time_to_search = next(iter(match_dict.items()))
            time_to_search = int(time_to_search) - GameSearching.TIMEOUT
            if time_to_search > 0:
                self.redis.decrease_tts(username, -GameSearching.TIMEOUT)
            else:
                match_dict['Bot'] = 0
                await self.send_invites(match_dict)
                match_dict = {}

            logger.debug(f'Match dict: {match_dict}')

        logger.debug('End check match')

    async def send_invites(self, match_dict):
        logger.debug('Start')
        room_token = self.room_manager.generate_room_token()
        logger.debug(f'Room token: {room_token}')
        usernames = list(match_dict.keys())
        logger.debug(f'Usernames: {usernames}')
        message = {
            'event_type': '/game_match',
            'message': f'Game found: P1 - {usernames[0]}, P2 - {usernames[1]}',
            'target_url': f'/game_lobby/{room_token}/',
        }

        logger.debug(message)

        for user in usernames:
            if user == 'Bot':
                new_bot = Bot()
                game = GameHandler.get_or_add(room_token)
                game.set_observer(new_bot)
                await game.set_character(new_bot)
            else:
                await GameSearching.OBSERVERS[user].game_match(message)
                GameSearching.OBSERVERS.pop(user)
                self.redis.delete_search(user)



