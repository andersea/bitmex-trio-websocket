# -*- coding: utf-8 -*-

"""Top-level package for BitMEX Trio-Websocket."""

__author__ = """Anders Ellenshøj Andersen"""
__email__ = 'andersa@atlab.dk'
__version__ = '0.4.2'

from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional
import logging

import trio
import ujson

from .websocket import connect
from .storage import Storage

log = logging.getLogger(__name__)

class BitMEXWebsocket:
    def __init__(self):
        self.storage = Storage()
        self.trio_websocket = None
        self._listeners = defaultdict(list)
        self._listeners_attached = trio.Event()
    
    @staticmethod
    @asynccontextmanager
    async def connect(network: str, api_key: str=None, api_secret: str=None):

        if not network in ('mainnet', 'testnet'):
            raise ValueError('network argument must be either \'mainnet\' or \'testnet\'')


        async def process_stream():
            log.debug('Run task starting.')
            # log.debug('Websocket connected. Waiting for listeners.')
            await bitmex_websocket._listeners_attached.wait()
            try:
                async for item, item_symbol, item_table, item_action in stream:
                    for listen_table, listen_symbol in bitmex_websocket._listeners.keys():
                        if listen_table == item_table:
                            if item_symbol:
                                if not listen_symbol or listen_symbol == item_symbol:
                                    for send_channel in bitmex_websocket._listeners[(listen_table, listen_symbol)]:
                                        await send_channel.send(item)
                            else:
                                for send_channel in bitmex_websocket._listeners[(listen_table, listen_symbol)]:
                                    await send_channel.send(item)
            finally:
                log.debug('Stream processing task done.')
        
        bitmex_websocket = BitMEXWebsocket()

        async with trio.open_nursery() as nursery:
            stream = bitmex_websocket.storage.process(connect(nursery, network, api_key, api_secret))
            bitmex_websocket.trio_websocket = await stream.__anext__()
            nursery.start_soon(process_stream)
            yield bitmex_websocket
            log.debug('BitMEXWebsocket context exit. Cancelling running tasks.')
            nursery.cancel_scope.cancel()
        log.debug('BitMEXWebsocket closed.')

    async def listen(self, table: str, symbol: Optional[str]=None):
        send_channel, receive_channel = trio.open_memory_channel(0)
        listener = (table, symbol)
        if not listener in self._listeners:
            topic = table
            if symbol:
                topic += f':{symbol}'
            await self.trio_websocket.send_message(ujson.dumps({'op': 'subscribe', 'args': [topic]}))
        self._listeners[listener].append(send_channel)
        self._listeners_attached.set()
        try:
            while True:
                yield await receive_channel.receive()
        finally:
            log.debug('Listener detached from table: %s, symbol: %s', table, symbol)
            self._listeners[listener].remove(send_channel)
