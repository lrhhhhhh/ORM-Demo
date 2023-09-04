import sys
import datetime
from abc import ABC, abstractmethod


class NoneValue:
    pass


class Field(ABC):
    def __set_name__(self, owner, name):
        self.field_name = name

    def __get__(self, instance, owner):
        try:
            return instance.kv_map[self.field_name]
        except AttributeError:
            raise RuntimeError(f'model field `{self.field_name}` is not assigned', )

    def __set__(self, instance, value):
        self.validate(value)
        instance.kv_map[self.field_name] = self.format(value)

    @classmethod
    def generate_ddl(
            cls,
            field_name,
            column_type,
            primary_key=False,
            default=None,
            auto_increment=False,
            unique=False,
            *args
    ):
        li = [field_name, column_type]
        if primary_key:
            li.append('PRIMARY KEY')
        if default is not None:
            if isinstance(default, (int, float, bool)):
                li.append(f'DEFAULT {default}')
            else:
                # todo: bug when default type is not int or float
                raise Exception('Unknown type')
        if unique:
            li.append('UNIQUE')
        if auto_increment:
            li.append('AUTO_INCREMENT')
        li.extend(args)
        return ' '.join(li)

    @abstractmethod
    def validate(self, value):
        # if not pass the validation, raise Error
        pass

    @abstractmethod
    def ddl(self) -> str:
        pass

    @abstractmethod
    def format(self, value) -> [int, float, str, bool, None,]:
        # must guarantee the value is legal
        pass


class Integer(Field):
    def __init__(
        self,
        column_type='INTEGER',
        default=None,
        primary_key=False,
        unique=False,
        auto_increment=False,
        minvalue=-sys.maxsize-1,
        maxvalue=sys.maxsize,
    ):
        self.column_type = column_type
        self.default = default
        self.unique = unique
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.primary_key = primary_key
        self.auto_increment = auto_increment

    def ddl(self):
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=self.column_type,
            primary_key=self.primary_key,
            auto_increment=self.auto_increment,
            default=self.default,
            unique=self.unique
        )

    def validate(self, value):
        if value is None:    # auto increment
            self.auto_increment = True
        elif isinstance(value, int) and self.minvalue <= value <= self.maxvalue:
            pass
        else:
            raise ValueError(f'integer validation fail, value is {value}')

    def format(self, value) -> [int, float, str, bool, None]:
        if value is None:   # when value equals `None`, it represents value `NULL` in mysql
            return value
        else:
            return int(value)


class Double(Field):
    def __init__(
        self,
        column_type='DOUBLE',
        m=None,
        d=None,
        primary_key=False,
        default=None,
        unique=False,
    ):
        self.column_type = column_type
        self.m = m
        self.d = d
        self.primary_key = primary_key
        self.default = default
        self.unique = unique

    def ddl(self):
        if self.m and self.d:
            column_type = f'{self.column_type}({self.m}, {self.d})'
        else:
            column_type = self.column_type
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=column_type,
            primary_key=self.primary_key,
            default=self.default,
            unique=self.unique,
        )

    def validate(self, value):
        try:
            float(value)
        except ValueError as e:
            raise ValueError(f'Double validation fail at value {value}')

    def format(self, value) -> [int, float, str, bool, None]:
        return float(value)


class String(Field):
    def __init__(
        self,
        max_length,
        column_type='VARCHAR',
        primary_key=False,
        default=None,
        unique=False,
    ):
        self.max_length = max_length
        self.primary_key = primary_key
        self.column_type = column_type
        self.default = default
        self.unique = unique

    def ddl(self):
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=f'{self.column_type}({self.max_length})',
            primary_key=self.primary_key,
            default=self.default,
            unique=self.unique,
        )

    def validate(self, value):
        if isinstance(value, str) and len(value) <= self.max_length:
            return
        raise ValueError(f'string validation fail at value {value}')

    def format(self, value) -> [int, float, str, None, bool]:
        return value


class Boolean(Field):
    def __init__(
        self,
        column_type='boolean',
        default=None,
        primary_key=False,
        unique=False,
    ):
        self.column_type = column_type
        self.default = default
        self.primary_key = primary_key
        self.unique = unique

    def ddl(self):
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=self.column_type,
            primary_key=self.primary_key,
            default=self.default,
            unique=self.unique,
        )

    def validate(self, value):
        if isinstance(value, int):
            if value == 1:
                value = True
            elif value == 0:
                value = False
            else:
                raise ValueError(f'only valid when value=1 or value=0')
        if value is not True and value is not False:
            raise ValueError(f'True or False are expected, got {type(value)}')

    def format(self, value) -> [int, float, str, bool, None]:
        return value


class Date(Field):
    def __init__(
        self,
        column_type='DATE',
        default=None,
        primary_key=False,
        unique = False,
    ):
        self.column_type = column_type
        self.default = default
        self.primary_key = primary_key
        self.unique = unique

    def ddl(self):
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=self.column_type,
            default=self.default,
            unique=self.unique,
        )

    def validate(self, value):
        if isinstance(value, datetime.date):
            pass
        elif isinstance(value, str):
            try:
                datetime.date.fromisoformat(value)   # YYYY-MM-DD
            except ValueError as e:
                raise ValueError('invalid Date formation, must be YYYY-MM-DD')
        else:
            raise Exception('unknown Error at Date Validation')

    def format(self, value) -> [int, float, str, bool, None]:
        if isinstance(value, datetime.date):
            return value.isoformat()
        else:
            return value


class DateTime(Field):
    def __init__(
        self,
        column_type='DATETIME',
        default=None,
        primary_key=False,
        unique=False
    ):
        self.column_type = column_type
        self.default = default
        self.primary_key = primary_key
        self.unique = unique

    def ddl(self):
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=self.column_type,
            default=self.default,
            primary_key=self.primary_key,
            unique=self.unique,
        )

    def validate(self, value):
        if isinstance(value, datetime.datetime):
            pass
        elif isinstance(value, str):
            try:
                datetime.datetime.fromisoformat(value)
            except ValueError as e:
                raise ValueError('invalid Datetime formation, must be YYYY-MM-DD HH:MM:SS.mmmmmm')

    def format(self, value) -> [int, float, str, bool, None]:
        if isinstance(value, datetime.datetime):
            return value.isoformat(sep=' ')
        else:
            return value


class TimeStamp(Field):
    def __init__(
        self,
        column_type='TIMESTAMP',
        default=None,
        primary_key=False,
        unique=False
    ):
        self.column_type = column_type
        self.default = default
        self.primary_key = primary_key
        self.unique = unique

    def ddl(self):
        return self.generate_ddl(
            field_name=self.field_name,
            column_type=self.column_type,
            default=self.default,
            primary_key=self.primary_key,
            unique=self.unique,
        )

    def validate(self, value):
        if isinstance(value, datetime.datetime):
            pass
        elif isinstance(value, int):
            datetime.datetime.fromtimestamp(value)
        else:
            raise TypeError('timestamp expect: int or datetime.datetime')

    def format(self, value) -> [int, float, str, bool, None]:
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, int):
            return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
