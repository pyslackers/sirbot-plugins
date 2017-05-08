"""
Hookspecs of the slack plugin
"""

import pluggy

hookspec = pluggy.HookspecMarker('sirbot.github')


@hookspec
def register_github_events():
    """
    Events hook
    """
    pass
