import pymysql
import logging
from PyORM.sql import sql_map


def create_engine(user='', password='', host='localhost', port=3306, **kwargs):
    return pymysql.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        **kwargs
    )


def create_db(user: str, password: str, host: str, port: int, db: str):
    conn = create_engine(user, password, host, port)
    sql = sql_map['__create_db__'].format(db_name=db)
    execute_sql(conn, sql)


def execute_sql(connection: pymysql.Connection, sql, values=None):
    if connection is None:
        raise RuntimeError('require db connection, got None')
    logging.debug(f'\nexecute sql:\n{sql} \nwith values:{values}')

    try:
        cursor = connection.cursor()
        affected = cursor.execute(sql, values)
        result = cursor.fetchall()
        cursor.close()
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e

    msg = f'affected: {affected}\n'
    if affected == 0:
        msg = msg + 'Attention! nothing happen after execute sql\n'
    logging.debug(msg)
    return result
