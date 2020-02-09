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
from bitmex_trio_websocket import BitMEXWebsocket, connect

async def test_auth_fail():
    await trio.sleep(random())
    try:
        async with trio.open_nursery() as nursery:
            async with aclosing(connect(nursery, 'testnet', 'abcd1234', 'efgh5678')) as agen:
                async for msg in agen:
                    assert False
    except ConnectionRejected:
        assert True

async def test_auth_success():
    await trio.sleep(random())
    try:
        async with trio.open_nursery() as nursery:
            messages = connect(nursery, 'testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'))
            async with aclosing(messages) as agen:
                ws = await agen.__anext__()
                assert isinstance(ws, WebSocketConnection)
                await ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['margin', 'position', 'order', 'execution']}))
                async for msg in agen:
                    assert isinstance(msg, dict)
                    assert 'action' in msg
                    await ws.aclose()

    except ConnectionClosed:
        assert True

async def test_multisymbol():
    await trio.sleep(random())
    try:
        async with trio.open_nursery() as nursery:
            messages = connect(nursery, 'testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'))
            count = 0
            async with aclosing(messages) as agen:
                ws = await agen.__anext__()
                await ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['instrument:XBTUSD', 'instrument:ETHUSD']}))
                async for msg in agen:
                    assert isinstance(msg, dict)
                    count += 1
                    if count >= 3:
                        print(count)
                        await ws.aclose()
    except ConnectionClosed:
        assert True

async def test_context_manager():
    async with BitMEXWebsocket.connect('testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET')) as bitmex_ws:
        count = 0
        async with aclosing(bitmex_ws.listen('instrument', 'XBTUSD')) as agen:
            async for msg in agen:
                count += 1
                if count >= 3:
                    break
            assert True

async def test_orderbook():
    async with BitMEXWebsocket.connect('testnet') as bws:
        async with aclosing(bws.listen('orderBookL2', 'XBTUSD')) as agen:
            async for msg in agen:
                assert len(msg) == 2
                break

async def test_network_argument():
    async with BitMEXWebsocket.connect('mainnet') as s:
        assert getattr(s, 'listen', None) is not None
    async with BitMEXWebsocket.connect('testnet') as s:
        assert getattr(s, 'listen', None) is not None
    with pytest.raises(ValueError):
        async with BitMEXWebsocket.connect('incorrect') as s:
            assert False, 'BitMEXWebsocket.connect accepted erroneous network argument.'
