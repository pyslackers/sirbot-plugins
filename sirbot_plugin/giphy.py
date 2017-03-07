import os
import aiohttp
import random
import logging

from sirbot.plugin import Plugin
from sirbot.hookimpl import hookimpl

logger = logging.getLogger('sirbot.giphy')


@hookimpl
def plugins(loop):
    return 'giphy', GiphyPlugin(loop)


class GiphyPlugin(Plugin):
    def __init__(self, loop):
        super().__init__(loop)
        self._session = None
        self._token = os.environ.get('SIRBOT_GIPHY_TOKEN') or "dc6zaTOxFJmzC"
        self._loop = loop

    def configure(self, config, router, facades):
        if 'loglevel' in config:
            logger.setLevel(config['logleve'])

    async def start(self):
        self._session = aiohttp.ClientSession(loop=self._loop)
        pass

    def facade(self):
        return Giphy(token=self._token, session=self._session)

    def __del__(self):
        if self._session:
            self._session.close()


class Giphy:
    ROOT_URL = 'http://api.giphy.com/v1/{}'
    SEARCH_TERM_URL = ROOT_URL.format('gifs/translate?s={terms}')
    TRENDING_URL = ROOT_URL.format('gifs/trending?')
    RANDOM_URL = ROOT_URL.format('gifs/random?')
    BY_ID_URL = ROOT_URL.format('gifs/{gif_id}?')

    def __init__(self, token, session):
        self._token = token
        self._session = session

    async def search(self, terms):
        data = await self._query(self.SEARCH_TERM_URL.format(terms='+'.join(terms)))
        return data['data']['images']['original']['url']

    async def trending(self):
        data = await self._query(self.TRENDING_URL)
        num = random.randint(0, len(data['data']) - 1)
        return data['data'][num]['images']['original']['url']

    async def random(self):
        data = await self._query(self.RANDOM_URL)
        num = random.randint(0, len(data['data']) - 1)
        return data['data']['image_url']

    async def by_id(self, id_):
        data = await self._query(self.BY_ID_URL.format(gif_id=id_))
        return data['data']['images']['original']['url']

    async def _query(self, url, method='GET'):
        if url.endswith('?'):
            url += 'api_key={}'.format(self._token)
        else:
            url += '&api_key={}'.format(self._token)

        logger.debug('Query giphy api with url: %s', url)
        rep = await self._session.request(method, url)
        data = await rep.json()

        if data['meta']['status'] != 200:
            raise ConnectionError
        return data
