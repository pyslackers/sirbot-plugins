from sirbot.core import hookimpl
from .github import GitHubPlugin


@hookimpl
def plugins(loop):
    return GitHubPlugin(loop)
