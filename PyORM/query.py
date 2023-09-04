from PyORM.sql import sql_map
from PyORM.utils import execute_sql


class QueryDescriptor:
    def __set__(self, instance, value):
        raise RuntimeError('never assign value to `Model.query`')

    def __get__(self, instance, owner):
        return Query(model_class=owner)


class Query:
    def __init__(self, model_class, bind=None):
        self.model_class = model_class
        self.bind = bind

    def __call__(self, bind):
        cls = self.__class__
        return cls(model_class=self.model_class, bind=bind)

    def execute(self, sql, values=None):
        return execute_sql(self.bind, sql, values)

    def select_all(self):
        sql = sql_map['__select_all__'].format(table_name=self.model_class.table_name)
        return self.execute(sql)

    @classmethod
    def filter(cls):
        pass

    def filter_by(self, **kwargs) -> list:
        """
        filter_by() 只支持`=`(等号)判等运算
        :param kwargs: 查询条件
        :return: 返回满足条件的记录构成的列表
        """
        if not kwargs:
            raise RuntimeError('**kwargs is required')

        sql_template = sql_map['__select__'].format(
            table_name=self.model_class.table_name,
            condition=','.join([f'{k}={"%s"}' for k in kwargs.keys()])
        )

        records = self.execute(sql_template, tuple(kwargs.values()))

        result = list()
        for record in records:
            tmp = self.model_class(**dict(zip(self.model_class.__kd_map__.keys(), record)))
            tmp.read_from_db = True
            result.append(tmp)
        return result

