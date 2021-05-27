import logging

import pymysql
from threading import Timer, Lock
from queue import Queue


class Pool:
    """
    数据库连接池（未完成）
    功能：
    1. 创建一个指定大小的数据库连接池
    2. 获取一个数据库连接
    3. 动态保持连接池的大小

    难点：
    1. 如何回收连接（用户得手动释放连接）
    2. 如何避免连接池的代码入侵其他代码
    """
    def __init__(
        self,
        user,
        password,
        db,
        host='localhost',
        port=3306,
        minsize=1,
        maxsize=7,
        timeout=5,
        interval=1.0,
        autocommit=False
    ):
        self.user = user
        self.password = password
        self.db = db
        self.host = host
        self.port = port
        self.minsize = minsize
        self.maxsize = maxsize
        self.interval = interval
        self.timeout = timeout
        self.autocommit = autocommit

        self.mutex = Lock()
        self.busy_connect = set()
        self.idle_connect = Queue(maxsize=self.maxsize)
        for i in range(self.maxsize):
            self.idle_connect.put(self.create_a_connect())

        # start a watch dog to maintain the size of pool
        self.watch_dog = Timer(interval=self.interval, function=self.watch, args=(self.idle_connect, self.busy_connect))
        self.watch_dog.run()

    def create_a_connect(self):
        return pymysql.connect(
            user=self.user,
            password=self.password,
            db=self.db,
            host=self.host,
            port=self.port,
            connect_timeout=self.timeout,
            autocommit=self.autocommit
        )

    def watch(self, idle_connect: Queue, busy_connect: Queue):
        sz = idle_connect.qsize() + busy_connect.qsize()
        if sz < self.maxsize:
            for i in range(self.maxsize-sz):
                self.idle_connect.put(self.create_a_connect())

    def acquire_conn(self):
        with self.mutex:
            conn = self.idle_connect.get(timeout=self.timeout)
            if conn not in self.busy_connect:
                self.busy_connect.add(conn)
                return conn, (self.release_conn, self)
            raise RuntimeError('connection is busy! release it first')

    @staticmethod
    def release_conn(pool, conn):
        with pool.mutext:
            pool.idle_connect.put(conn)
            pool.busy_connct.remove(conn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.watch_dog.cancel()
        while not self.idle_connect.empty():
            fr = self.idle_connect.get()
            fr.close()

        if len(self.busy_connect) != 0:
            logging.critical('some connection are still working, but the pool was closed')
        for conn in list(self.busy_connect):
            conn.close()
