import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class _Cursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, parameters=()):
        return self._cursor.execute(query.replace("?", "%s"), parameters)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class _Connection:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        return _Cursor(self._connection.cursor())

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()


def connect(timeout=10):
    conninfo = os.getenv("DATABASE_URL")
    if conninfo:
        connection = psycopg.connect(
            conninfo,
            row_factory=dict_row,
            connect_timeout=timeout,
        )
    else:
        connection = psycopg.connect(
            row_factory=dict_row,
            connect_timeout=timeout,
        )
    return _Connection(connection)
