import aiohttp
import logging

from aiohttp_xmlrpc.client import ServerProxy
from distance import levenshtein
from operator import itemgetter

from sirbot.plugin import Plugin
from sirbot.hookimpl import hookimpl

logger = logging.getLogger('sirbot.pypi')


@hookimpl
def plugins(loop):
    return 'pypi', PyPiPlugin(loop)


class PyPiPlugin(Plugin):
    ROOT_URL = 'https://pypi.python.org/pypi'

    def __init__(self, loop):
        super().__init__(loop)
        self._session = None
        self._client = None
        self._loop = loop
        self._started = False

    async def configure(self, config, router, session, facades):
        self._session = session

    async def start(self):
        self._client = ServerProxy(self.ROOT_URL, loop=self._loop, client=self._session)
        self._started = True

    def facade(self):
        return PyPi(session=self._session, client=self._client)

    @property
    def started(self):
        return self._started


class PyPi:
    SEARCH_PATH = '?%3Aaction=search&term={0}&submit=search'
    ROOT_URL = 'https://pypi.python.org/pypi'

    def __init__(self, session, client):
        self._session = session
        self.client = client

    async def pypi_search(self, term):
        results = await self.client.search({'name': term})
        for item in results:
            item['distance'] = levenshtein(str(term), item["name"])
        results.sort(key=itemgetter('distance'))
        return results
