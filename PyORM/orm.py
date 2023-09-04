from abc import ABCMeta
from PyORM.fields import Field, NoneValue
from PyORM.sql import sql_map
from PyORM.query import Query, QueryDescriptor
from PyORM.utils import execute_sql


class ModelMeta(ABCMeta):
    def __new__(mcs, name, bases, attrs):
        if name == 'Model':
            return type.__new__(mcs, name, bases, attrs)

        kd_map = dict()           # field_name, field_descriptor map
        primary_key = None
        unique_keys = list()
        for k, v in attrs.items():
            if isinstance(v, Field):
                kd_map[k] = v
                if v.unique:
                    unique_keys.append(k)
                if primary_key and v.primary_key:
                    raise AttributeError('duplicate primary key')
                elif not primary_key and v.primary_key:
                    primary_key = k

        attrs['__kd_map__'] = kd_map
        attrs['__primary_key__'] = primary_key
        attrs['__unique_key__'] = unique_keys

        return type.__new__(mcs, name, bases, attrs)


class Model(metaclass=ModelMeta):

    table_name = ''
    query = QueryDescriptor()

    def __init__(self, **kwargs):
        self.read_from_db = False
        self.kv_map = dict.fromkeys(self.__kd_map__.keys(), NoneValue)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        getattr(self, item)

    def __repr__(self):
        k_v = [f'{k}={v}' for k, v in self.kv_map.items()]
        return f'{self.__class__}({",".join(k_v)})'

    def keys(self) -> tuple:
        """
        :return: 返回数据库记录各列的列名
        """
        return tuple(self.kv_map.keys())

    def values(self) -> tuple:
        """
        :return: 返回数据库记录各个字段的值组成的元组
        """
        return tuple(self.kv_map.values())

    @classmethod
    def ddl(cls):
        """
        :return: 返回数据表的定义语句
        """
        fields_ddl = [v.ddl() for k, v in cls.__kd_map__.items()]
        sql = sql_map['__create__'].format(
            table_name=cls.table_name,
            fields=',\n    '.join(fields_ddl)
        )
        return sql

    @classmethod
    def execute(cls, connection, sql, values=None):
        return execute_sql(connection, sql, values)

    @classmethod
    def create_table(cls, connection):
        cls.execute(connection, cls.ddl())

    @classmethod
    def drop_table(cls, connection):
        sql = sql_map['__drop__'].format(table_name=cls.table_name)
        cls.execute(connection, sql)


if __name__ == '__main__':
    print(Model.__dict__)
