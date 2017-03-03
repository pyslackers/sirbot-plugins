import pluggy
import logging
import importlib
import inspect

from . import hookspecs


logger = logging.getLogger('sirbot.web')


class Client:
    def __init__(self, loop, queue):
        self._loop = loop
        self._queue = queue
        self._router = None
        self._config = None
        self._pm = None

    def configure(self, config, router):
        self._router = router
        self._config = config or {}

        if 'loglevel'in self._config:
            logger.setLevel(self._config['loglevel'])

        self._initialize_plugins()
        self._register_route(self._router)

    async def connect(self):
        pass

    def _initialize_plugins(self):
        logger.debug('Initializing web plugins')
        self._pm = pluggy.PluginManager('sirbot.web')
        self._pm.add_hookspecs(hookspecs)

        for plugin in self._config.get('plugins'):
            p = importlib.import_module(plugin)
            self._pm.register(p)

    def _register_route(self, router):
        all_endpoints = self._pm.hook.register_web_endpoints()
        for endpoints in all_endpoints:
            for endpoint in endpoints:
                logger.debug('Registering new endpoints: %s for %s on %s in %s',
                             endpoint['func'].__name__,
                             endpoint['method'], endpoint['url'],
                             inspect.getabsfile(endpoint['func']))
                router.add_route(
                    endpoint['method'],
                    endpoint['url'],
                    endpoint['func']
                )
