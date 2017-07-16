import logging

from sirbot.core import hookimpl, Plugin
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


@hookimpl
def plugins(loop):
    return SchedulerPlugin(loop)


class SchedulerPlugin(Plugin):
    __name__ = 'apscheduler'
    __version__ = '0.0.1'
    __registry__ = 'scheduler'

    def __init__(self, loop):
        super().__init__(loop)
        self._config = None
        self._scheduler = None
        self._loop = loop
        self._started = False

    async def configure(self, config, router, session):
        logger.debug('Configuring scheduler plugin')
        self._config = config
        self._scheduler = AsyncIOScheduler(event_loop=self._loop)

    async def start(self):
        self._scheduler.start()
        self._started = True

    def factory(self):
        return self._scheduler

    @property
    def started(self):
        return self._started
