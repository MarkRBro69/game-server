import datetime

from mongoengine import Document, DateTimeField, StringField, DictField


class GameModel(Document):
    game_date = DateTimeField(default=datetime.datetime.now)
    game_log = StringField()
    # Players usernames, game result (winner, ratings change)
    game_result = DictField(required=True)

    meta = {
        'indexes': ['game_date']
    }
