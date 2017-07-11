import logging
import sqlite3
import os
import yaml

from sirbot.core import Plugin, hookimpl
from sirbot.utils import merge_dict

logger = logging.getLogger(__name__)


@hookimpl
def plugins(loop):
    return SQLitePlugin(loop)


class SQLitePlugin(Plugin):
    __name__ = 'sqlite'
    __version__ = '0.0.1'
    __registry__ = 'database'

    def __init__(self, loop):
        super().__init__(loop)
        self._loop = loop
        self._config = None
        self._started = False
        self._connection = None

    async def configure(self, config, router, session):

        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'config.yml'
        )

        with open(path) as file:
            defaultconfig = yaml.load(file)

        self._config = merge_dict(config, defaultconfig[self.__name__])
        self._connection = sqlite3.connect(self._config['file'])
        self._connection.row_factory = sqlite3.Row

        db = self._connection.cursor()
        db.execute('''
                   CREATE TABLE IF NOT EXISTS metadata
                   (
                   plugin TEXT PRIMARY KEY,
                   version TEXT
                   )
                   ''')
        self._connection.commit()

    async def start(self):
        self._started = True

    def factory(self):
        return SQLiteWrapper(self._connection, self._connection.cursor())

    @property
    def started(self):
        return self._started

    async def update(self, config, sirbot_plugins):
        file = config.get('file', None)
        if not file:
            return
        if not os.path.isfile(file):
            return

        self._connection = sqlite3.connect(file)
        self._connection.row_factory = sqlite3.Row
        db = self.factory()

        await db.execute('''SELECT * FROM metadata''')
        metadata = await db.fetchall()
        metadata = {
            plugin: {'version': version} for plugin, version in metadata
        }

        for name, plugin in sirbot_plugins.items():
            database_update = getattr(
                plugin['plugin'], 'database_update', None
            )
            if callable(database_update):
                plugin_metadata = metadata.get(name, {})
                old_version = plugin_metadata.get('version')
                current_version = plugin['plugin'].__version__

                if current_version != old_version:
                    logger.debug('Updating database of %s from %s to %s',
                                 name, old_version, current_version)
                    await database_update(
                        metadata.get(name, {}), self.factory()
                    )
                    await db.execute('''INSERT OR REPLACE INTO
                                        metadata (plugin, version)
                                        VALUES (?, ?)''',
                                     (name, current_version)
                                     )

        self._connection.commit()

    def __del__(self):
        if self._connection:
            self._connection.close()


class SQLiteWrapper:
    def __init__(self, connection, cursor):
        self._connection = connection
        self.cursor = cursor
        self.type = 'sqlite'

    async def execute(self, sql, params=tuple()):
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

    async def set_plugin_metadata(self, plugin):
        await self.execute('''SELECT * FROM metadata WHERE plugin = ?''',
                           (plugin.__name__,))
        old_metadata = await self.fetchone()

        if old_metadata and old_metadata['version'] != plugin.__version__:
            logger.error(
                '''Database not updated for plugin %s version %s.
                 Please run `sirbot update` before continuing''',
                plugin.__name__, plugin.__version__)
        elif not old_metadata:
            await self.execute('''INSERT OR REPLACE INTO
                                  metadata (plugin, version) VALUES (?, ?)''',
                               (plugin.__name__, plugin.__version__))

    def __del__(self):
        self.cursor.close()
