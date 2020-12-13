# -*- coding: utf-8 -*-

"""Top-level package for BitMEX Trio-Websocket."""

__author__ = """Anders Ellenshøj Andersen"""
__email__ = 'andersa@atlab.dk'
__version__ = '0.10.4'

from .websocket import open_bitmex_websocket, BitMEXWebsocket
from .storage import MemoryStorage, PostgresStorage
from .logger import Logger
from .statistics import Statistics
