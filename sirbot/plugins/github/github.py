import logging
import os
import yaml
import asyncio
import inspect
import hmac
import hashlib

from aiohttp.web import Response
from collections import defaultdict

from sirbot.core import Plugin, registry
from sirbot.utils import merge_dict, ensure_future

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
        self._router = None
        self._dispatcher = None
        self._verification = None

    async def configure(self, config, router, session):
        logger.debug('Configuring github plugin')

        self._verification = os.environ.get('SIRBOT_GITHUB_SECRET')
        if not self._verification:
            raise GitHubSetupError('SIRBOT_GITHUB_SECRET NOT SET')
        else:
            self._verification = self._verification.encode()

        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'config.yml'
        )

        with open(path) as file:
            defaultconfig = yaml.load(file)

        self._config = merge_dict(config, defaultconfig[self.__name__])

        self._session = session
        self._config = config
        self._router = router

        self._dispatcher = GitHubDispatcher(
            config=self._config,
            verification=self._verification,
            loop=self._loop
        )

        logger.debug('Adding github endpoint: %s', self._config['endpoint'])
        self._router.add_route(
            'POST',
            self._config['endpoint'],
            self._dispatcher.incoming
        )

        self._started = True

    def factory(self):
        return GitHubWrapper(self._dispatcher)

    async def start(self):
        pass

    @property
    def started(self):
        return self._started


class GitHubWrapper:
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher

    def add_event(self, event, func):
        self._dispatcher.register(event, func)


class GitHubDispatcher:

    def __init__(self, config, verification, loop):
        self._config = config
        self._loop = loop
        self._verification = verification

        self._events = defaultdict(list)

    async def incoming(self, request):

        signature = request.headers.get('X-Hub-Signature')
        event_type = request.headers.get('X-GitHub-Event')
        event_id = request.headers.get('X-GitHub-Delivery')
        raw = await request.read()

        sign = signature.split('=')[1]
        verify = hmac.new(
            self._verification,
            msg=raw,
            digestmod=hashlib.sha1
        )
        if not hmac.compare_digest(str(verify.hexdigest()), sign):
            return Response(status=401)

        event = await request.json()
        event['id'] = event_id
        event['type'] = event_type

        logger.debug('Github handler received "%s"', event['type'])

        funcs = self._events.get(event['type'], list())
        logger.debug('%s handlers found for "%s"', len(funcs), event['type'])
        for func in funcs:
            f = func(event, registry.get('github'))
            ensure_future(coroutine=f, loop=self._loop, logger=logger)

        return Response(status=200)

    def register(self, event, func):
        logger.debug('Registering event: %s, %s from %s',
                     event,
                     func.__name__,
                     inspect.getabsfile(func))

        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        self._events[event].append(func)
