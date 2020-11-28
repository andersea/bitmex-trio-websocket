#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `bitmex_trio_websocket` package."""
import os
from random import random

import pytest

import trio
from async_generator import aclosing
import ujson
import pendulum
from trio_websocket import ConnectionRejected, WebSocketConnection, ConnectionClosed
from bitmex_trio_websocket import open_bitmex_websocket, BitMEXWebsocket
from slurry import Pipeline, Group

async def test_auth_fail():
    with pytest.raises(ConnectionRejected):
        async with open_bitmex_websocket('testnet', 'abcd1234', 'efgh5678') as bws:
            async with aclosing(bws.listen('position')) as aiter:
                async for item in aiter:
                    assert False
                    

# async def test_auth_success():
#     bitmex_websocket = BitMEXWebsocket()
#     try:
#         async with bitmex_websocket._connect('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'), False):
#             async with aclosing(bitmex_websocket._websocket_parser()) as agen:
#                 assert isinstance(bitmex_websocket._ws, WebSocketConnection)
#                 await bitmex_websocket._ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['margin', 'position', 'order', 'execution']}))
#                 async for msg in agen:
#                     assert isinstance(msg, dict)
#                     assert 'action' in msg
#                     await bitmex_websocket._ws.aclose()
#     except ConnectionClosed as e:
#         assert e.reason.code == 1000

# async def test_multisymbol():
#     bitmex_websocket = BitMEXWebsocket()
#     try:
#         async with bitmex_websocket._connect('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'), False):
#             count = 0
#             async with aclosing(bitmex_websocket._websocket_parser()) as agen:
#                 await bitmex_websocket._ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['instrument:XBTUSD', 'instrument:ETHUSD']}))
#                 async for msg in agen:
#                     assert isinstance(msg, dict)
#                     count += 1
#                     if count >= 3:
#                         print(count)
#                         await bitmex_websocket._ws.aclose()
#     except ConnectionClosed as e:
#         assert e.reason.code == 1000

# async def test_context_manager():
#     async with open_bitmex_websocket('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET')) as bitmex_ws:
#         count = 0
#         async with aclosing(bitmex_ws.listen('instrument', 'XBTUSD')) as agen:
#             async for msg in agen:
#                 count += 1
#                 if count >= 3:
#                     break
#             assert True

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

async def test_funding():
    async with open_bitmex_websocket('mainnet') as ws:
        async with Pipeline.create(
            Group(2, ws.listen('funding'))
        ) as pipeline, pipeline.tap() as aiter:
            async for bundle in aiter:
                for funding in bundle:
                    funding['timestamp'] = pendulum.parse(funding['timestamp'])
                    funding['fundingInterval'] = pendulum.parse(funding['fundingInterval'])
                assert isinstance(bundle, tuple)
                assert len(bundle) > 1
                return
            assert False, 'This should not happen.'
