from abc import ABC, abstractmethod
import sqlite3
from sqlite3 import OperationalError


class Field(ABC):
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return instance.connection.execute(
            f'SELECT {self.name} FROM {instance.table_name} WHERE {instance.key}={instance.key_value}'
        ).fetchone()[0]

    def __set__(self, instance, value):

        self.validate(value)

        if not instance.key_value:
            instance.connection.execute(f'INSERT INTO {instance.table_name}({self.name}) VALUES(?);', [value])
            instance.connection.commit()

            # 使用row_id 在并发时可能出问题
            row_id = instance.connection.execute(f'SELECT last_insert_rowid() FROM {instance.table_name}').fetchone()[0]
            last_insert = instance.connection.execute(
                f'SELECT * FROM {instance.table_name} LIMIT 1 OFFSET {row_id - 1};'
            ).fetchone()
            instance.key_value = last_insert[0]
        else:
            fmt = f"UPDATE {instance.table_name} SET {self.name}=%r WHERE {instance.key}=%r;"
            sql = fmt % (value, instance.key_value)
            instance.connection.execute(sql)
            instance.connection.commit()


    @abstractmethod
    def validate(self, value):
        pass

    @abstractmethod
    def ddl(self):
        pass

class Integer(Field):
    def __init__(self, minvalue, maxvalue, primary_key=False, auto_increment=False):
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.primary_key = primary_key
        self.auto_increment = auto_increment

    def ddl(self):
        if self.primary_key:
            if self.auto_increment:
                return f'{self.name} INTEGER PRIMARY KEY AUTOINCREMENT'
            else:
                return f'{self.name} INTEGER PRIMARY KEY'
        else:
            return f'{self.name} INTEGER'

    def validate(self, value):
        if value is None:     # auto increment
            pass
        elif isinstance(value, int) and self.minvalue <= value <= self.maxvalue:
            pass
        else:
            raise AttributeError('integer validation fail')

class String(Field):
    def __init__(self, max_length, primary_key=False):
        self.max_length = max_length
        self.primary_key = primary_key

    def ddl(self):
        if self.primary_key:
            return f'{self.name} VARCHAR({self.max_length}) PRIMARY KEY'
        else:
            return f'{self.name} VARCHAR({self.max_length})'

    def validate(self, value):
        if isinstance(value, str) and len(value) <= self.max_length:
            pass
        else:
            raise AttributeError('string validation fail')


class User:
    connection = None
    table_name = 'users'
    key = 'uid'
    key_value = None

    uid = Integer(minvalue=0, maxvalue=100, auto_increment=True, primary_key=True)
    username = String(max_length=64)
    age = Integer(minvalue=0, maxvalue=200)

    def __init__(self, username, age):
        self.uid = None
        self.username = username
        self.age = age

    @classmethod
    def create_table(cls):
        fields = []
        fmt = 'CREATE TABLE {table_name}({fields})'
        for k, v in vars(cls).items():
            if isinstance(v, Field):
                fields.append(v.ddl())
        ddl = fmt.format(
            table_name = cls.table_name,
            fields = ','.join(fields)
        )

        print(ddl)
        try:
            cls.connection.execute(ddl)
            cls.connection.commit()
        except OperationalError as e:
            if 'already exists' in str(e):
                print(e)
            else:
                raise OperationalError('unknown error')

    @classmethod
    def register(cls, connection):
        cls.connection = connection

    @classmethod
    def select_all(cls):
        return cls.connection.execute(f"select * from {cls.table_name};").fetchall()

    def __repr__(self):
        return f'User(uid={self.uid}, username={self.username}, age={self.age})'


if __name__ == '__main__':
    with sqlite3.connect('user.db') as connection:
        User.register(connection)
        User.create_table()
        u1 = User(username='Tom', age=18)
        u2 = User(username='XiaoMing', age=19)
        print(u1, u2)
        User.select_all()

