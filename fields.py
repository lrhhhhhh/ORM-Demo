from abc import ABC, abstractmethod
import sys


class Field(ABC):
    def __set_name__(self, owner, name):
        self.field_name = name
        self.field_value = None
        self.field_flag = False

    def __get__(self, instance, owner):
        return self.field_value

    def __set__(self, instance, value):
        self.validate(value)
        self.field_value = value
        self.field_flag = True


    @abstractmethod
    def validate(self, value):
        pass

    @abstractmethod
    def ddl(self):
        pass


class Integer(Field):
    def __init__(
            self,
            column_type = 'Integer',
            default = 0,
            primary_key = False,
            auto_increment = False,
            minvalue = -sys.maxsize-1,
            maxvalue = sys.maxsize,
    ):
        self.column_type = column_type
        self.default = default
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.primary_key = primary_key
        self.auto_increment = auto_increment

    def ddl(self):

        if self.primary_key:
            if self.auto_increment:
                return f'{self.field_name} {self.column_type} PRIMARY KEY AUTOINCREMENT'
            else:
                return f'{self.field_name} {self.column_type} PRIMARY KEY'
        else:
            return f'{self.field_name} {self.column_type}'

    def validate(self, value):
        if value is None:     # auto increment
            pass
        elif isinstance(value, int) and self.minvalue <= value <= self.maxvalue:
            pass
        else:
            raise AttributeError('integer validation fail')

class String(Field):
    def __init__(self, max_length=128, column_type='VARCHAR', primary_key=False):
        self.max_length = max_length
        self.primary_key = primary_key
        self.column_type = column_type


    def ddl(self):
        if self.primary_key:
            return f'{self.field_name} {self.column_type}({self.max_length}) PRIMARY KEY'
        else:
            return f'{self.field_name} {self.column_type}({self.max_length})'

    def validate(self, value):
        if isinstance(value, str) and len(value) <= self.max_length:
            pass
        else:
            raise AttributeError('string validation fail', value)



