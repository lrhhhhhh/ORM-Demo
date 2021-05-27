import logging
from contextvars import ContextVar
from SimpleORM.fields import NoneValue
from SimpleORM.utils import create_engine
from SimpleORM.sql import sql_map


class Session:
    __slots__ = ('__local', '__config')

    def __init__(self, config: dict):
        object.__setattr__(self, '_Session__local', ContextVar("db_session"))
        object.__setattr__(self, '_Session__config', config)
        self.setitem('connect', self.create_new_engine())

    def create_new_engine(self):
        return create_engine(**self.__config)

    @property
    def connection(self):
        connect = self.getitem('connect', None)
        if not connect:
            connect = self.create_new_engine()
        return connect

    def get_current_session(self):
        return self.__local.get({})

    def setitem(self, key, value):
        values = self.__local.get({})
        values[key] = value
        self.__local.set(values)

    def getitem(self, item, default=None):
        values = self.__local.get({})
        return values.get(item, default)

    def add(self, records):
        queue = self.getitem('queue', [])
        if not isinstance(records, list):
            records = [records]
        if isinstance(records, list):
            operations = list()
            for record in records:
                if record.read_from_db:
                    operations.append(('update', record))
                else:
                    operations.append(('insert', record))
            queue.extend(operations)
            self.setitem('queue', queue)

    def remove(self, records):
        queue = self.getitem('queue', [])
        if not isinstance(records, list):
            records = [records]
        if isinstance(records, list):
            queue.extend([('delete', record) for record in records])
            self.setitem('queue', queue)

    def commit(self):
        queue = self.getitem('queue', [])
        for operate, record in queue:
            if operate == 'insert':
                self._insert_one(record)
            elif operate == 'update':
                self._update_one(record)
            elif operate == 'delete':
                self._delete_one(record)
            else:
                raise RuntimeError('invalid operation')
        self.setitem('queue', [])

    def close(self):
        self.getitem('connect').close()
        self.__local.set({})

    def _execute(self, sql, values=None):
        if self.connection is None:
            raise RuntimeError('require db connection, got None')

        logging.debug(f'\nexecute sql:\n{sql} \nwith values:{values}')

        try:
            cursor = self.connection.cursor()
            affected = cursor.execute(sql, values)
            result = cursor.fetchall()
            cursor.close()
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

        logging.debug(f'affected: {affected}')
        if affected == 0:
            logging.debug('Attention! nothing happen after execute sql')
        return result

    def _insert_one(self, record):
        values = record.values()
        placeholder = ["%s"] * len(values)

        sql_template = sql_map['__insert__'].format(
            table_name=record.table_name,
            fields=','.join(record.kv_map.keys()),
            values=','.join(placeholder)
        )
        self._execute(sql_template, values)

    def _insert_many(self, records: list):
        assert len(records) > 0
        cls = records[0].__class__
        template = '(' + ','.join(["%s"] * len(cls.__kd_map__.keys())) + ')'

        sql = sql_map['__insert_many__'].format(
            table_name=cls.table_name,
            fields=','.join(cls.__kd_map__.keys()),
            values=',\n'.join([template] * len(records))
        )

        args = list()
        for each in records:
            if type(each) != cls:
                raise ValueError(f'insert_many() required the same Model, got {type(each)}')
            args.extend(each.values())
        self._execute(sql, tuple(args))

    def _update_one(self, record, **kwargs):
        primary_key_value = record.kv_map.get(record.__primary_key__)
        unchanged_fields = set(record.kv_map.keys()) - set(kwargs.keys())
        set_kv = dict()
        where_kv = dict()
        if kwargs:
            set_kv = kwargs
            for unchanged_field in unchanged_fields:
                where_kv[unchanged_field] = record.kv_map.get(unchanged_field)
            record.kv_map.update(kwargs)
        elif record.__primary_key__:
            if primary_key_value is not NoneValue:
                where_kv[record.__primary_key__] = primary_key_value
                for k, v in record.kv_map.items():
                    if k != record.__primary_key__:
                        set_kv[k] = v
            else:
                raise RuntimeError("missing primary key's value")
        else:
            raise Exception(
                '1. no primary key exists, \n '
                '2. no unchanged field exists or no kwargs provided \n'
                'please check the usage of update()'
            )

        sql_template = sql_map['__update__'].format(
            table_name=record.table_name,
            fields=','.join([f'{k}={"%s"}' for k in set_kv.keys()]),
            clause=' AND '.join([f'{k}={"%s"}' for k in where_kv.keys()])
        )
        values = list()
        values.extend(set_kv.values())
        values.extend(where_kv.values())
        self._execute(sql_template, values)

    def _delete_one(self, record):
        clause = ' AND '.join(f'{k}={"%s"}' for k, v in record.kv_map.items())
        sql_template = sql_map['__delete__'].format(
            table_name=record.table_name,
            clause=clause
        )
        self._execute(sql_template, tuple(record.kv_map.values()))



