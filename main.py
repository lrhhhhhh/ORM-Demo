import sqlite3
import logging

from orm import Model
from fields import Integer, String

class User(Model):
    table_name = 'user'
    uid = Integer(primary_key=True)
    username = String(max_length=32)

    def __init__(self, username, uid=None):
        self.username = username
        self.uid = uid

    def __repr__(self):
        return f'User{self.uid, self.username}'

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    with sqlite3.connect('user.db') as connection:
        User.register(connection)
        User.create_table()
        u = User(username='lrhaoo')
        u.insert_record()
        print(u)
        u.select_all()

        u2 = User.filter_by(uid=1)
        print(u2)
        u2.username = 'Tom'
        u.update_record()
        u.select_all()
