#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `bitmex_trio_websocket` package."""
import os
from random import random

import pytest

import trio
from async_generator import aclosing
import ujson
from trio_websocket import ConnectionRejected, WebSocketConnection, ConnectionClosed
from bitmex_trio_websocket import open_bitmex_websocket, BitMEXWebsocket

async def test_auth_fail():
    bitmex_websocket = BitMEXWebsocket()
    with pytest.raises(ConnectionRejected):
        async with bitmex_websocket._connect('testnet', 'abcd1234', 'efgh5678', False) as bws:
            async with aclosing(bws._websocket_parser()) as agen:
                async for message in agen:
                    assert False
                    

async def test_auth_success():
    bitmex_websocket = BitMEXWebsocket()
    async with bitmex_websocket._connect('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'), False):
        async with aclosing(bitmex_websocket._websocket_parser()) as agen:
            assert isinstance(bitmex_websocket._ws, WebSocketConnection)
            await bitmex_websocket._ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['margin', 'position', 'order', 'execution']}))
            async for msg in agen:
                assert isinstance(msg, dict)
                assert 'action' in msg
                await bitmex_websocket._ws.aclose()

async def test_multisymbol():
    bitmex_websocket = BitMEXWebsocket()
    async with bitmex_websocket._connect('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'), False):
        count = 0
        async with aclosing(bitmex_websocket._websocket_parser()) as agen:
            await bitmex_websocket._ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['instrument:XBTUSD', 'instrument:ETHUSD']}))
            async for msg in agen:
                assert isinstance(msg, dict)
                count += 1
                if count >= 3:
                    print(count)
                    await bitmex_websocket._ws.aclose()

async def test_context_manager():
    async with open_bitmex_websocket('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET')) as bitmex_ws:
        count = 0
        async with aclosing(bitmex_ws.listen('instrument', 'XBTUSD')) as agen:
            async for msg in agen:
                count += 1
                if count >= 3:
                    break
            assert True

async def test_orderbook():
    async with open_bitmex_websocket('testnet') as bws:
        async with aclosing(bws.listen('orderBookL2', 'XBTUSD')) as agen:
            async for msg in agen:
                assert len(msg) == 2
                break

async def test_network_argument():
    async with open_bitmex_websocket('mainnet') as s:
        assert getattr(s, 'listen', None) is not None
    async with open_bitmex_websocket('testnet') as s:
        assert getattr(s, 'listen', None) is not None
    with pytest.raises(ValueError):
        async with open_bitmex_websocket('incorrect') as s:
            assert False, 'BitMEXWebsocket.connect accepted erroneous network argument.'
