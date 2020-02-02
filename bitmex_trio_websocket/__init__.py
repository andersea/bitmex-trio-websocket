# -*- coding: utf-8 -*-

"""Top-level package for BitMEX Trio-Websocket."""

from contextlib import asynccontextmanager, AsyncExitStack
from typing import Union, Iterable, Optional

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
        self._exit_stack = AsyncExitStack()
        self._listeners = []
        self._listeners_attached = trio.Event()
    
    @staticmethod
    @asynccontextmanager
    async def connect(endpoint: str, symbol: Union[str, Iterable[str]]=None, api_key: str=None, api_secret: str=None):

        async def run(bitmex_websocket, ready):
            stream = bitmex_websocket.storage.process(connect(endpoint, symbol, api_key, api_secret))
            bitmex_websocket.trio_websocket = await stream.__anext__()
            ready.set()
            await bitmex_websocket._listeners_attached.wait()
            async for item, item_symbol, item_table, item_action in stream:
                for listen_table, listen_symbol, send_channel in bitmex_websocket._listeners:
                    if listen_table == item_table:
                        if item_symbol:
                            if not listen_symbol or listen_symbol == item_symbol:
                                await send_channel.send(item)
                        else:
                            await send_channel.send(item)
                await bitmex_websocket._listeners_attached.wait()
        
        bitmex_websocket = BitMEXWebsocket()
        ready = trio.Event()
        async with trio.open_nursery() as nursery, bitmex_websocket._exit_stack:
            nursery.start_soon(run, bitmex_websocket, ready)
            await ready.wait()
            yield bitmex_websocket
            nursery.cancel_scope.cancel()
    
    async def listen(self, table: str, symbol: Optional[str]=None):
        send_channel, receive_channel = trio.open_memory_channel(0)
        await self._exit_stack.enter_async_context(send_channel)
        self._listeners.append((table, symbol, send_channel))
        self._listeners_attached.set()
        try:
            async for item in receive_channel:
                yield item
        finally:
            self._listeners.remove((table, symbol, send_channel))
            if not self._listeners:
                self._listeners_attached = trio.Event()
