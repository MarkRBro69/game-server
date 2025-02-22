import asyncio

from game_app.utils import RedisServer, RoomManager


class GameSearching:
    _instance = None

    TIMEOUT = 5
    LOOP_LIMIT = 100
    SHOULD_RESTART = False
    LOOP_TASK = None
    OBSERVERS = {}
    REDIS = RedisServer()
    ROOM_MANAGER = RoomManager()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, username, observer):
        GameSearching.OBSERVERS[username] = observer
        if GameSearching.LOOP_TASK is None:
            GameSearching.LOOP_TASK = asyncio.create_task(self.check_loop())
        else:
            GameSearching.SHOULD_RESTART = True

    async def check_loop(self):
        for _ in range(GameSearching.LOOP_LIMIT):
            if GameSearching.SHOULD_RESTART:
                GameSearching.SHOULD_RESTART = False
                await self.restart_loop()
                return

            self.check_match()
            await asyncio.sleep(GameSearching.TIMEOUT)

        GameSearching.LOOP_TASK = None

    async def restart_loop(self):
        if GameSearching.LOOP_TASK:
            GameSearching.LOOP_TASK.cancel()
            try:
                await GameSearching.LOOP_TASK
            except asyncio.CancelledError:
                pass

        GameSearching.LOOP_TASK = asyncio.create_task(self.check_loop())

    def check_match(self):
        searching_users = GameSearching.REDIS.get_all_search()

        match_list = {}
        for username, time_to_search in searching_users:
            if len(match_list) < 2:
                match_list[username] = time_to_search
            else:
                self.send_invites(match_list)
                match_list = {}

        if len(match_list) == 1:
            username, time_to_search = match_list.popitem()
            time_to_search -= GameSearching.TIMEOUT
            if time_to_search > 0:
                GameSearching.REDIS.decrease_tts(username, -GameSearching.TIMEOUT)
            else:
                pass
                # self.send_invites(match_list)

    @staticmethod
    def send_invites(match_list):
        room_token = GameSearching.ROOM_MANAGER.generate_room_token()
        usernames = match_list.keys()
        message = {
            'event_type': 'game_match',
            'message': f'Game found: P1 - {usernames[0]}, P2 - {usernames[1]}',
            'target_url': f'/game_lobby/{room_token}/',
        }
        for user in usernames:
            GameSearching.OBSERVERS[user].game_match(message)
            GameSearching.OBSERVERS.pop(user)



