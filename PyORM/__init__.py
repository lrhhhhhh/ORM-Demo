from PyORM.orm import Model
from PyORM.utils import create_engine
from PyORM.session import Session


class PyORM:
    def __init__(
            self,
            user='',
            password='',
            database='',
            host='localhost',
            port=3306,
            autocommit=False,
            **kwargs
    ):
        self.config = dict()
        self.config['user'] = user
        self.config['password'] = password
        self.config['database'] = database
        self.config['host'] = host
        self.config['port'] = port
        self.config['autocommit'] = autocommit
        self.config.update(kwargs)

        # self.Model = type('PyORM.Model', Model.__bases__, dict(Model.__dict__))
        self.Model = Model
        self.session = Session(config=self.config)

    def create_all(self):
        conn = create_engine(**self.config)
        for cls in self.Model.__subclasses__():
            cls.create_table(conn)
        conn.commit()
        conn.close()

    def drop_all(self):
        conn = create_engine(**self.config)
        for cls in self.Model.__subclasses__():
            cls.drop_table(conn)
        conn.commit()
        conn.close()




