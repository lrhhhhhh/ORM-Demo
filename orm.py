import logging

from abc import ABCMeta
from collections import UserDict
from fields import Field

class ModelMeta(ABCMeta):
    def __new__(mcs, name, bases, attrs):

        if name == 'Model':
            return type.__new__(mcs, name, bases, attrs)

        kv_map = dict()
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                kv_map[k] = v
                if primary_key and v.primary_key:
                    raise AttributeError('duplicate primary key')
                elif not primary_key and v.primary_key:
                    primary_key = k

        attrs['__map__'] = kv_map
        attrs['__fields__'] = kv_map.keys()
        attrs['__primary_key__'] = primary_key

        attrs['__create__'] = 'CREATE TABLE {table_name}({fields});'
        attrs['__insert__'] = 'INSERT INTO {table_name}({fields}) VALUES ({values});'
        attrs['__update__'] = 'UPDATE {table_name} SET {fields} WHERE {primary_key}=?;'

        return type.__new__(mcs, name, bases, attrs)


class Model(UserDict, metaclass=ModelMeta):
    table_name = None
    connection = None

    def __init__(self, **kwargs):
        super(Model, self).__init__(kwargs)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        getattr(self, item)

    @classmethod
    def register(cls, connection):
        cls.connection = connection

    @classmethod
    def create_table(cls):
        fields_ddl = [v.ddl() for k, v in cls.__map__.items()]
        sql = cls.__create__.format(
            table_name=cls.table_name,
            fields=','.join(fields_ddl)
        )
        cls.execute(cls.connection, sql, [])

    def select_all(self):
        res = self.connection.execute(f'SELECT * FROM {self.table_name};').fetchall()
        print(f"table {self.table_name}'s records: {res}")

    @classmethod
    def filter_by(cls, **kwargs):
        """
        目前WHERE只支持`=`(等号)运算
        :param kwargs: condition
        :return: cls(record)
        """
        fmt = 'SELECT * FROM {table_name} WHERE {condition};'
        condition = list()
        for k, v in kwargs.items():
            condition.append(f'{k}={v}')
        sql = fmt.format(
            table_name = cls.table_name,
            condition = ','.join(condition)
        )
        record = cls.connection.execute(sql).fetchone()

        return cls(**dict(zip(cls.__fields__, record)))

    @staticmethod
    def execute(connection, sql, values=None):
        logging.debug((sql, values))
        cursor = connection.cursor()
        cursor.execute(sql, values)
        affected = cursor.rowcount
        connection.commit()
        logging.debug(f'affected: {affected}')

    def insert_record(self):
        values = list()
        placeholder = list()
        for k, v in self.__map__.items():
            if not v.field_flag:
                raise AttributeError(f'table {self.table_name} missing field {k}')
            placeholder.append('?')
            values.append(v.field_value)

        sql = self.__insert__.format(
            table_name = self.table_name,
            fields = ','.join(self.__fields__),
            values = ','.join(placeholder)
        )
        self.execute(self.connection, sql, values)


    def update_record(self):
        primary_key_value = self.__map__.get(self.__primary_key__).field_value
        if not primary_key_value:
            raise RuntimeError("missing primary key's value, please read from database first")
        fields = list()
        values = list()

        for k, v in self.__map__.items():
            if v.field_flag:
                fields.append(f'{k}=?')
                values.append(v.field_value)
        values.append(primary_key_value)

        sql = self.__update__.format(
            table_name = self.table_name,
            fields = ','.join(fields),
            primary_key = self.__primary_key__
        )
        self.execute(self.connection, sql, values)









