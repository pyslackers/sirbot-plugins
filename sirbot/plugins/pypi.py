import logging

from aiohttp_xmlrpc.client import ServerProxy
from distance import levenshtein
from operator import itemgetter

from sirbot.core import hookimpl, Plugin

logger = logging.getLogger(__name__)


@hookimpl
def plugins(loop):
    return PyPiPlugin(loop)


class PyPiPlugin(Plugin):
    __name__ = 'pypi'
    __version__ = '0.0.1'
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
        self._client = ServerProxy(
            self.ROOT_URL,
            loop=self._loop,
            client=self._session
        )
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

    async def search(self, term):
        results = await self.client.search({'name': term})
        for item in results:
            item['distance'] = levenshtein(str(term), item["name"])
        results.sort(key=itemgetter('distance'))
        return results
