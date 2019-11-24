# BitMEX Trio-Websocket


[![PyPI](https://img.shields.io/pypi/v/bitmex_trio_websocket.svg)](https://pypi.python.org/pypi/bitmex-trio-websocket)
[![Build Status](https://img.shields.io/travis/com/andersea/bitmex-trio-websocket.svg)](https://travis-ci.com/andersea/bitmex-trio-websocket)
[![Read the Docs](https://readthedocs.org/projects/bitmex-trio-websocket/badge/?version=latest)](https://bitmex-trio-websocket.readthedocs.io/en/latest/?badge=latest)

Websocket implementation for BitMEX cryptocurrency derivatives exchange.

* Free software: MIT license
* Documentation: https://bitmex-trio-websocket.readthedocs.io.

## Features

* Connects to BitMEX websockets for a given symbol or lists of symbols.
* Supports authenticated connections using api keys.
* Fully async using async generators. No callbacks or event emitters.
* Based on trio and trio-websocket.

## Installation

This library requires Python 3.7 or greater. It could probably be made to run with Python 3.6, since this
is the minimal version where async generators are supported. To install from PyPI:

    pip install bitmex-trio-websocket

## Client example

    import trio

    from bitmex_trio_websocket import BitMEXWebsocket

    async def main():
        bws = BitMEXWebsocket('mainnet', 'XBTUSD')
        async for message in bws.start():
            print(message)

    trio.run(main)

This will print a sequence of tuples of the form `(item, symbol|None, table, action)`, where -

`item` is the full object resulting from inserting or merging the changes to an item.
 
`symbol` is the symbol that was changed or `None` if the table isn't a symbol table.

`table` is the table name.

`action` is the action that was taken.

Note, that delete actions are simply applied and consumed, with no output sent.

## API

&nbsp;&nbsp;&nbsp;&nbsp; ![bitmex__trio__websocket.BitMEXWebsocket](https://img.shields.io/badge/class-bitmex__trio__websocket.BitMEXWebsocket-blue?style=flat-square)

> ![constructor](https://img.shields.io/badge/constructor-BitMEXWebsocket(endpoint%2C%20symbol%2C%20api__key%2C%20api__secret)-blue)
>
> Creates a new websocket object.
>
> **`endpoint`** str
>> Network to connect to. Options: 'mainnet', 'testnet'.
>
> **`symbol`** Optional\[Union\[str, Iterable\[str\]\]\]
>> Symbols to subscribe to. Each symbol is subscribed to the following channels: ['instrument', 'quote', 'trade', 'tradeBin1m']. If not provided, no instrument channels are subscribed for this connection. This may be useful if you only want to connect to authenticated channels.
>
> **`api_key`** Optional\[str\]
>> Api key for authenticated connections. If a valid api key and secret is supplied, the following channels are subscribed: ['margin', 'position', 'order', 'execution'].
>
> **`api_secret`** Optional\[str\]
>> Api secret for authenticated connections.

> ![await start](https://img.shields.io/badge/await-start()-darkgreen)
>
> Returns an async generator object that yields messages from the websocket.

> ![storage](https://img.shields.io/badge/property-storage-404040)
>
> This property contains the storage object for the websocket. The storage object has two properties `data` and `keys`. `data` contains the table state for each channel as a dictionary with the table name as key. The tables themselves are flat lists. `keys` contains a list of keys by which to look up values in each table. There is a helper function `findItemByKeys` in the storage unit, which assists in finding particular items in each table. Tables are searched sequentially until a match is found, with is somewhat inefficient. However since there is never a lot of records in each table (at most 200), this is reasonably fast in practice and not a bottleneck.

> ![ws](https://img.shields.io/badge/property-ws-404040)
>
> When connected, contains the underlying trio-websocket object. Can be used to manage the connection.
>
> See - https://trio-websocket.readthedocs.io/en/stable/api.html#connections

## Credits

Thanks to the [Trio](https://github.com/python-trio/trio) and [Trio-websocket](https://github.com/HyperionGray/trio-websocket) libraries for their awesome work.

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
