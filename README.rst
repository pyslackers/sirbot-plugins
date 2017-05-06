=========================
Plugins for Sir-bot-a-lot
=========================

|build|

`Sir-bot-a-lot`_ plugins built for the people and by the people of the `python developers slack community`_.

Want to join? `Get an invite`_ !

.. _Get an invite: http://pythondevelopers.herokuapp.com/
.. _python developers slack community: https://pythondev.slack.com/
.. |build| image:: https://travis-ci.org/pyslackers/sirbot-plugin.svg?branch=master
    :alt: Build status
    :target: https://travis-ci.org/pyslackers/sirbot-plugin

Installation
------------

**WARNING** plugins requires `sir-bot-a-lot`_.

The sources for sirbot-plugins can be downloaded from the `github repo`_.

.. code-block:: console

    $ git clone https://github.com/pyslackers/sirbot-plugins

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ pip install git+https://github.com/pyslackers/sir-bot-a-lot
    $ pip install sirbot-plugins/

To install the development requirements do:

.. code-block:: console

    $ pip install sirbot-plugins/[dev]

.. _sir-bot-a-lot: http://sir-bot-a-lot.readthedocs.io/en/latest/
.. _github repo: https://github.com/pyslackers/sirbot-plugins

Configuration
-------------

SQLite
^^^^^^

The default configuration for sirbot-sqlite look like this:

.. code-block:: yaml

    sqlite:
      file: ':memory:'
