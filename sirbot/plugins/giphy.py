import os
import random
import logging

from sirbot.core.plugin import Plugin
from sirbot.core.hookimpl import hookimpl

logger = logging.getLogger('sirbot.giphy')


@hookimpl
def plugins(loop):
    return GiphyPlugin(loop)


class GiphyPlugin(Plugin):
    __name__ = 'giphy'
    __version__ = '0.0.1'

    def __init__(self, loop):
        super().__init__(loop)
        self._session = None
        self._token = os.environ.get('SIRBOT_GIPHY_TOKEN') or "dc6zaTOxFJmzC"
        self._loop = loop

    async def configure(self, config, router, session, facades):
        self._session = session

    async def start(self):
        pass

    def facade(self):
        return Giphy(token=self._token, session=self._session)

    @property
    def started(self):
        return True


class Giphy:
    ROOT_URL = 'http://api.giphy.com/v1/{}'
    SEARCH_TERM_URL = ROOT_URL.format('gifs/search?q={terms}')
    TRENDING_URL = ROOT_URL.format('gifs/trending?')
    RANDOM_URL = ROOT_URL.format('gifs/random?')
    BY_ID_URL = ROOT_URL.format('gifs/{gif_id}?')

    def __init__(self, token, session):
        self._token = token
        self._session = session

    async def search(self, *terms):
        data = await self._query(
            self.SEARCH_TERM_URL.format(terms='+'.join(terms))
        )
        urls = [result['images']['original']['url'] for result in data['data']]
        return urls

    async def trending(self):
        data = await self._query(self.TRENDING_URL)
        num = random.randint(0, len(data['data']) - 1)
        return data['data'][num]['images']['original']['url']

    async def random(self):
        data = await self._query(self.RANDOM_URL)
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
