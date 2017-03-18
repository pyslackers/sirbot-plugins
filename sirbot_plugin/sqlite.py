import logging
import sqlite3

from sirbot.plugin import Plugin
from sirbot.hookimpl import hookimpl

logger = logging.getLogger('sirbot.sqlite')


@hookimpl
def plugins(loop):
    return 'database', SQLitePlugin(loop)


class SQLitePlugin(Plugin):
    def __init__(self, loop):
        super().__init__(loop)
        self._loop = loop

        self._started = False
        self._connection = None

    async def configure(self, config, router, session, facades):
        file = config.get('file', ':memory:')
        self._connection = sqlite3.connect(file)
        self._connection.row_factory = sqlite3.Row

    async def start(self):
        self._started = True

    def facade(self):
        return SQLiteFacade(self._connection, self._connection.cursor())

    @property
    def started(self):
        return self._started

    def __del__(self):
        self._connection.close()


class SQLiteFacade:
    def __init__(self, connection, cursor):
        self._connection = connection
        self.cursor = cursor

    async def execute(self, sql, params=[]):
        logger.debug('''Executing query: %s''', sql)
        self.cursor.execute(sql, params)

    async def commit(self):
        self._connection.commit()

    async def rollback(self):
        self._connection.rollback()

    async def fetchone(self):
        return self.cursor.fetchone()

    async def fetchmany(self, size):
        return self.cursor.fetchmany(size)

    async def fetchall(self):
        return self.cursor.fetchall()

    def __del__(self):
        self.cursor.close()
