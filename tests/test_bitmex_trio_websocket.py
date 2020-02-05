#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `bitmex_trio_websocket` package."""
import os
from random import random

import pytest

import trio
import ujson
from trio_websocket import ConnectionRejected, WebSocketConnection, ConnectionClosed
from bitmex_trio_websocket import BitMEXWebsocket, connect

async def test_auth_fail():
    await trio.sleep(random())
    try:
        async with trio.open_nursery() as nursery:
            async for msg in connect(nursery, 'testnet', 'abcd1234', 'efgh5678'):
                assert False
    except ConnectionRejected:
        assert True

async def test_auth_success():
    await trio.sleep(random())
    try:
        async with trio.open_nursery() as nursery:
            messages = connect(nursery, 'testnet', os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'))
            ws = await messages.__anext__()
            assert isinstance(ws, WebSocketConnection)
            await ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['margin', 'position', 'order', 'execution']}))
            async for msg in messages:
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
            ws = await messages.__anext__()
            await ws.send_message(ujson.dumps({'op': 'subscribe', 'args': ['instrument:XBTUSD', 'instrument:ETHUSD']}))
            async for msg in messages:
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
        async for msg in bitmex_ws.listen('instrument', 'XBTUSD'):
            count += 1
            if count >= 3:
                break
        assert True

async def test_orderbook():
    async with BitMEXWebsocket.connect('testnet') as bws:
        async for msg in bws.listen('orderBookL2', 'XBTUSD'):
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
