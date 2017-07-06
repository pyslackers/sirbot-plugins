import logging

from sirbot.core import hookimpl, Plugin

logger = logging.getLogger(__name__)


@hookimpl
def plugins(loop):
    return CandyPlugin(loop)


class CandyPlugin(Plugin):
    __name__ = 'candy'
    __version__ = '0.0.1'

    def __init__(self, loop):
        super().__init__(loop)
        self._started = False
        self._registry = None

    async def configure(self, config, router, session, registry):
        self._registry = registry

    async def start(self):
        await self._create_db_table()
        self._started = True

    def factory(self):
        return CandyWrapper(self._registry)

    @property
    def started(self):
        return self._started

    async def _create_db_table(self):
        db = self._registry.get('database')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS candy (
            user TEXT PRIMARY KEY NOT NULL,
            candy INT DEFAULT 0
            )
            ''')
        await db.set_plugin_metadata(self)
        await db.commit()

    async def database_update(self, metadata, db):
        return self.__version__


class CandyWrapper:
    def __init__(self, registry):
        self._registry = registry

    async def add(self, user, count=1):
        db = self._registry.get('database')
        await db.execute('''SELECT candy FROM candy WHERE user = ? ''',
                         (user, )
                         )
        value = await db.fetchone()
        if value:
            value = value['candy'] + count
        else:
            value = count

        await db.execute('''INSERT OR REPLACE INTO candy (user, candy)
                            VALUES (?, ?)''',
                         (user, value)
                         )
        await db.commit()
        return value

    async def top(self, count):
        db = self._registry.get('database')
        await db.execute('''SELECT * FROM candy ORDER BY candy DESC LIMIT ?''',
                         (count, )
                         )
        data = await db.fetchall()
        return data
