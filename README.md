# BitMEX Trio-Websocket


[![PyPI](https://img.shields.io/pypi/v/bitmex_trio_websocket.svg)](https://pypi.python.org/pypi/bitmex-trio-websocket)
[![Build Status](https://img.shields.io/travis/com/andersea/bitmex-trio-websocket.svg)](https://travis-ci.com/andersea/bitmex-trio-websocket)

Websocket implementation for BitMEX cryptocurrency derivatives exchange.

* Free software: MIT license

## Features

* Supports authenticated connections using api keys.
* Uses SortedDict as backend storage for easy and fast table searching.
* Fully async using async generators. No callbacks or event emitters.
* Based on [Slurry](https://slurry.readthedocs.io/en/latest/) and [Slurry-websocket](https://github.com/andersea/slurry-websocket). 

## Installation

This library requires Python 3.6 or greater. 

To install from PyPI:

    pip install bitmex-trio-websocket

## Client example

    import trio
    from async_generator import aclosing

    from bitmex_trio_websocket import open_bitmex_websocket

    async def main():
        async with open_bitmex_websocket('testnet') as bws:
            async with aclosing(bws.listen('instrument')) as agen:
                async for msg in agen:
                    print(f'Received message, symbol: \'{msg["symbol"]}\', timestamp: \'{msg["timestamp"]}\'')

    if __name__ == '__main__':
        trio.run(main)

This will print a sequence of dicts for each received item on inserts (including partials) or updates.

## API

![async def](https://img.shields.io/badge/async%20with-open__bitmex__websocket(network%2C%20api__key%2C%20api__secret%2C%20*%2C%20dead_mans_switch)-blue)

Creates a new websocket object.

This is an async context manager, so it needs to be used with the `async with .. as ..:` construct. The returned value is a BitMEXWebsocket object.

**`network`** str

Network to connect to. Options: 'mainnet', 'testnet'.

**`api_key`** Optional\[str\]

Api key for authenticated connections. 

**`api_secret`** Optional\[str\]

Api secret for authenticated connections.

**`dead_mans_switch`** Optional\[bool\]

When enabled, the websocket will periodically send cancelAllAfter messages with a timeout of 60 seconds. The timer is refreshed every 15 seconds.

See: https://www.bitmex.com/app/wsAPI#Dead-Mans-Switch-Auto-Cancel

![bitmex__trio__websocket.BitMEXWebsocket](https://img.shields.io/badge/class-bitmex__trio__websocket.BitMEXWebsocket-blue?style=flat-square)


![await listen](https://img.shields.io/badge/await-listen(table,%20symbol=None)-green)

Subscribes to the channel and optionally a specific symbol. It is possible for multiple listeners
to be listening using the same subscription.

Returns an async generator object that yields messages from the channel.

**`table`** str

Channel to subscribe to.

**`symbol`** Optional[str]

Optional symbol to subscribe to.

![storage](https://img.shields.io/badge/attribute-storage-teal)

This attribute contains the storage object for the websocket. The storage object caches the data tables for received
items. The implementation uses SortedDict from [Sorted Containers](http://www.grantjenks.com/docs/sortedcontainers/index.html),
to handle inserts, updates and deletes.

The storage object has two public attributes `data`, and `keys`.

`data` contains the table state for each channel as a dictionary with the table name as key. The tables are sorted dictionaries, stored with key tuples generated from each item using the keys schema received in the initial partial message.

`data['orderBookL2']` is a special state dictionary for the orderBookL2 table. It is a double nested defaultdict, with a SortedDict containing each price level. The nested dictionaries are composed like this:

    # Special storage for orderBookL2
    # dict[symbol][side][id]
    self.data['orderBookL2'] = defaultdict(lambda: defaultdict(SortedDict))

`keys` contains a mapping for lists of keys by which to look up values in each table.

In addition the following helper methods are supplied:

`make_key(table, match_data)` creates a key for searching the `data` table. Raises `ValueError` if `table == 'orderBookL2'`, since this table needs special indexing.

`parse_timestamp(timestamp)` static method for converting BitMEX timestamps to datetime with timezone (UTC).

## Credits

Thanks to the [Trio](https://github.com/python-trio/trio) and [Trio-websocket](https://github.com/HyperionGray/trio-websocket) libraries for their awesome work.

The library was originally based on the [reference client](https://github.com/BitMEX/api-connectors/tree/master/official-ws), but is now substantially redesigned.

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
