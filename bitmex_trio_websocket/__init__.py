# -*- coding: utf-8 -*-

"""Top-level package for BitMEX Trio-Websocket."""

from typing import Union, Iterable
from .websocket import connect
from .storage import Storage
from trio_websocket import WebSocketConnection

__author__ = """Anders Ellenshøj Andersen"""
__email__ = 'andersa@atlab.dk'
__version__ = '0.1.1'

class BitMEXWebsocket:
    def __init__(self, endpoint: str, symbol: Union[str, Iterable[str]]=None, api_key: str=None, api_secret: str=None):
        self.endpoint = endpoint
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.storage = Storage()
        self.ws = None
    
    async def start(self):
        connection = connect(self.endpoint, self.symbol, self.api_key, self.api_secret)
        async for message in self.storage.process():
            if not self.ws:
                self.ws = message
            else:
                yield message
    
