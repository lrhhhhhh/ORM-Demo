import time
import datetime
import logging

from PyORM import PyORM
from PyORM.fields import Integer, Double, String, Boolean, Date, DateTime, TimeStamp

logging.basicConfig(level=logging.DEBUG)

db = PyORM(
    user='root',
    password='123456',
    database='test_orm',
    host='localhost',
    port=3306,
)


class Student(db.Model):
    table_name = 'students'
    uid = Integer(primary_key=True, auto_increment=True)
    age = Integer(primary_key=False)
    height = Double(primary_key=False, m=5, d=3)
    username = String(primary_key=False, max_length=128)
    sex = Boolean(default=False)
    birthday = Date()
    last_seen = DateTime()
    timestamp = TimeStamp()

    def __init__(self, age, height, username, sex, birthday, last_seen, timestamp, uid=None):
        super().__init__()   # must do super().__init__() first
        self.uid = uid       # in order to support auto increment, must set uid=None
        self.age = age
        self.height = height
        self.username = username
        self.sex = sex
        self.birthday = birthday
        self.last_seen = last_seen
        self.timestamp = timestamp


class User(db.Model):
    table_name = 'users'
    uid = Integer(primary_key=True, auto_increment=True)
    username = String(max_length=32, unique=True)

    def __init__(self, username, uid=None):
        super().__init__()
        self.username = username
        self.uid = uid

    def __repr__(self):
        return f'User{self.uid, self.username}'


if __name__ == '__main__':
    db.drop_all()
    db.create_all()

    print(Student.ddl())
    print()
    print(User.ddl())

    s1 = Student(
        username=f'lrh',
        age=24,
        height=1.75,
        sex=True,
        birthday='1999-09-19',
        last_seen=datetime.datetime.now(),
        timestamp=int(time.time())
    )
    s2 = Student(
        username=f'mao',
        age=83,
        height=1.80,
        sex=True,
        birthday='1893-12-26',
        last_seen=datetime.datetime.now(),
        timestamp=int(time.time())
    )

    # insert
    db.session.add([s1, s2])
    u1 = User(username='xiao hong')
    db.session.add([u1])
    db.session.commit()

    print('-------------------insert--finish------------------------------')

    # check the result after insertion
    current_ctx_conn = db.session.connection
    print(Student.query(bind=current_ctx_conn).select_all())
    print(User.query(bind=current_ctx_conn).select_all())

    # query
    s3 = Student.query(bind=current_ctx_conn).filter_by(username='lrh')[0]
    u2 = User.query(bind=current_ctx_conn).filter_by(username='xiao hong')[0]
    print(s3)
    print(u2)
    print('------------------query--finish---------------------------------')

    # update
    u2.username = 'J.J.Cale'
    s3.username = 'Eric Clapton'
    db.session.add(u2)
    db.session.add(s3)
    db.session.commit()
    print(User.query(bind=current_ctx_conn).select_all())
    print(Student.query(bind=current_ctx_conn).select_all())
    print('------------------update-finish----------------------------------')

    # delete
    db.session.remove(u2)
    db.session.commit()
    print(User.query(bind=current_ctx_conn).select_all())
    print('-------------------delete-finish---------------------------------')

