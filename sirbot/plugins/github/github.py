import os
import yaml
import inspect
import asyncio
import logging

from gidgethub.aiohttp import GitHubAPI
from gidgethub.sansio import Event
from gidgethub import routing
from aiohttp.web import Response

from sirbot.core import Plugin
from sirbot.utils import merge_dict

from .errors import GitHubSetupError

logger = logging.getLogger(__name__)


class GitHubPlugin(Plugin):
    __name__ = 'github'
    __version__ = '0.0.1'

    def __init__(self, loop):
        super().__init__(loop)
        self._loop = loop
        self._started = False

        self._session = None
        self._config = None
        self._verification = None
        self._http_router = None
        self._github_router = None
        self._github_api = None

    async def configure(self, config, router, session):
        logger.debug('Configuring github plugin')

        self._verification = os.environ.get('SIRBOT_GITHUB_SECRET')
        if not self._verification:
            raise GitHubSetupError('SIRBOT_GITHUB_SECRET NOT SET')

        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'config.yml'
        )

        with open(path) as file:
            defaultconfig = yaml.load(file)

        self._config = merge_dict(config, defaultconfig[self.__name__])
        self._session = session
        self._http_router = router
        self._github_router = routing.Router()
        self._github_api = GitHubAPI(self._session, 'Sir-bot-a-lot')

        logger.debug('Adding github endpoint: %s', self._config['endpoint'])
        self._http_router.add_route(
            'POST',
            self._config['endpoint'],
            self._dispatch
        )

        self._started = True

    def factory(self):
        return GitHubWrapper(self._github_router)

    async def start(self):
        pass

    @property
    def started(self):
        return self._started

    async def _dispatch(self, request):
        try:
            event = Event.from_http(request.headers, await request.read(),
                                    secret=self._verification)
            await self._github_router.dispatch(event)
        except Exception as e:
            logger.exception(e)
            return Response(status=500)
        else:
            return Response(status=200)


class GitHubWrapper:
    def __init__(self, router):
        self._router = router

    def register(self, func, event_type, **kwargs):
        logger.debug('Registering event: %s, %s from %s',
                     event_type,
                     func.__name__,
                     inspect.getabsfile(func))
        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        self._router.add(func, event_type, **kwargs)
