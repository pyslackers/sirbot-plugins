import logging
import os
import yaml
import pluggy
import importlib
import asyncio
import inspect
import hmac
import hashlib

from aiohttp.web import Response
from collections import defaultdict

from sirbot.core import Plugin
from sirbot.utils import merge_dict, ensure_future

from . import hookspecs
from .errors import GitHubSetupError

logger = logging.getLogger(__name__)


class GitHubPlugin(Plugin):
    __name__ = 'github'
    __version__ = '0.0.1'

    def __init__(self, loop):
        self._loop = loop
        self._started = False

        self._session = None
        self._config = None
        self._router = None
        self._dispatcher = None
        self._facades = None
        self._verification = None

    async def configure(self, config, router, session, facades):
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
        self._facades = facades

        pm = self._initialize_plugins()

        self._dispatcher = Dispatcher(
            config=self._config,
            pm=pm,
            facades=self._facades,
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

    def _initialize_plugins(self):
        """
        Import and register the plugins

        Most likely composed of functions reacting to messages, events, slash
        commands and actions
        """
        logger.debug('Initializing handlers for github events')
        pm = pluggy.PluginManager('sirbot.github')
        pm.add_hookspecs(hookspecs)

        for plugin in self._config['plugins']:
            try:
                p = importlib.import_module(plugin)
                pm.register(p)
            except Exception as e:
                logger.exception(e)

        return pm

    async def start(self):
        pass

    @property
    def started(self):
        return self._started


class Dispatcher:

    def __init__(self, config, facades, pm, verification, loop):
        self._config = config
        self._facades = facades
        self._loop = loop
        self._verification = verification

        self._events = defaultdict(list)

        self._register(pm)

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
            facade = self._facades.new()
            f = func(event, facade)
            ensure_future(coroutine=f, loop=self._loop, logger=logger)

        return Response(status=200)

    def _register(self, pm):
        """
        Find and register the functions handling specifics events

        hookspecs: def register_github_events()

        :param pm: pluggy plugin manager
        :return None
        """
        all_events = pm.hook.register_github_events()
        for events in all_events:
            for event in events:
                if not asyncio.iscoroutinefunction(event['func']):
                    logger.debug('Function is not a coroutine, converting.')
                    event['func'] = asyncio.coroutine(event['func'])
                logger.debug('Registering github event: %s, %s from %s',
                             event['event'],
                             event['func'].__name__,
                             inspect.getabsfile(event['func']))
                self._events[event['event']].append(event['func'])
