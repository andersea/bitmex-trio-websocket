=====================
BitMEX Trio-Websocket
=====================


.. image:: https://img.shields.io/pypi/v/bitmex_trio_websocket.svg
        :target: https://pypi.python.org/pypi/bitmex_trio_websocket

.. image:: https://img.shields.io/travis/com/andersea/bitmex-trio-websocket.svg
        :target: https://travis-ci.com/andersea/bitmex-trio-websocket

.. image:: https://readthedocs.org/projects/bitmex-trio-websocket/badge/?version=latest
        :target: https://bitmex-trio-websocket.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Websocket implementation for BitMEX cryptocurrency derivatives exchange.


* Free software: MIT license
* Documentation: https://bitmex-trio-websocket.readthedocs.io.


Features
--------

* Connects to BitMEX websockets for a given symbol or lists of symbols.
* Supports authenticated connections using api keys.
* Fully async using async generators. No callbacks or event emitters.
* Based on trio and trio-websocket.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
