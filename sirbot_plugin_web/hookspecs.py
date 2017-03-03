"""
Hookspecs of the web plugin
"""

import pluggy

hookspec = pluggy.HookspecMarker('sirbot.web')


@hookspec
def register_web_endpoints():
    pass
