# -*- coding: utf-8 -*-

"""Top-level package for BitMEX Trio-Websocket."""

from contextlib import asynccontextmanager
from typing import Union, Iterable

import trio

from .websocket import connect
from .storage import Storage


__author__ = """Anders Ellenshøj Andersen"""
__email__ = 'andersa@atlab.dk'
__version__ = '0.2.8'

class BitMEXWebsocket:
    def __init__(self):
        self.storage = Storage()
        self.trio_websocket = None
        self._buffer = None
    
    @staticmethod
    @asynccontextmanager
    async def connect(endpoint: str, symbol: Union[str, Iterable[str]]=None, api_key: str=None, api_secret: str=None):

        async def run(bitmex_websocket, ready):
            stream  = bitmex_websocket.storage.process(connect(endpoint, symbol, api_key, api_secret))
            send_channel, receive_channel = trio.open_memory_channel(1)
            bitmex_websocket._buffer = receive_channel
            bitmex_websocket.trio_websocket = await stream.__anext__()
            ready.set()
            try:
                async for message in stream:
                    await send_channel.send(message)
            finally:
                await bitmex_websocket.trio_websocket.aclose()
        
        async with trio.open_nursery() as nursery:
            bitmex_websocket = BitMEXWebsocket()
            ready = trio.Event()
            nursery.start_soon(run, bitmex_websocket, ready)
            await ready.wait()
            yield bitmex_websocket
            nursery.cancel_scope.cancel()


    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self._buffer.receive()
