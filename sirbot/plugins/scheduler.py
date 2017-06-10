import logging

from sirbot.core import hookimpl, Plugin
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


@hookimpl
def plugins(loop):
    return SchedulerPlugin(loop)


class SchedulerPlugin(Plugin):
    __name__ = 'scheduler'
    __version__ = '0.0.1'

    def __init__(self, loop):
        super().__init__(loop)
        self._config = None
        self._facades = None
        self._scheduler = None

        self._loop = loop
        self._started = False

    async def configure(self, config, router, session, facades):
        logger.debug('Configuring scheduler plugin')
        self._config = config
        self._facades = facades

        self._scheduler = AsyncIOScheduler(event_loop=self._loop)

    async def start(self):
        self._scheduler.start()
        self._started = True

    def facade(self):
        return SchedulerFacade(
            scheduler=self._scheduler,
            facades=self._facades
        )

    @property
    def started(self):
        return self._started


class SchedulerFacade:

    def __init__(self, scheduler, facades):
        self.scheduler = scheduler
        self._facades = facades

    def add_job(self, func, trigger, args=None, *job_args, **job_kwargs):

        if not args:
            args = list()
        elif type(args) is tuple:
            args = list(args)

        args.insert(0, self._facades.new())
        self.scheduler.add_job(func, trigger=trigger, args=args,
                               *job_args, **job_kwargs)
