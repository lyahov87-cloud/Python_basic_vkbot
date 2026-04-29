from peewee import SqliteDatabase, Model, CharField, DateTimeField, ForeignKeyField, TextField
from datetime import datetime

db = SqliteDatabase('bot_history.db')

class User(Model):
    vk_id = CharField(unique=True)
    class Meta:
        database = db

class History(Model):
    user = ForeignKeyField(User, backref='history')
    command = CharField()
    query_text = TextField(null=True)
    timestamp = DateTimeField(default=datetime.now)
    class Meta:
        database = db

def init_db():
    db.connect()
    db.create_tables([User, History])
