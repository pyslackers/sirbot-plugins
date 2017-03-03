from .__meta__ import DATA as METADATA
from .client import Client

from sirbot.hookimpl import hookimpl


@hookimpl
def clients(loop, queue):
    return METADATA['name'], Client(loop=loop, queue=queue)
