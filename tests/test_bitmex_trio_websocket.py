#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `bitmex_trio_websocket` package."""
import os

from trio import sleep
from random import random
from trio_websocket import ConnectionRejected, WebSocketConnection, ConnectionClosed
from bitmex_trio_websocket import BitMEXWebsocket, connect

async def test_auth_fail():
    await sleep(random())
    try:
        async for msg in connect('testnet', None, None, 'abcd1234', 'efgh5678'):
            assert False
    except ConnectionRejected:
        assert True

async def test_auth_success():
    await sleep(random())
    try:
        messages = connect('testnet', None, None, os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'))
        ws = await messages.asend(None)
        assert isinstance(ws, WebSocketConnection)
        async for msg in messages:
            assert isinstance(msg, dict)
            assert 'action' in msg
            await ws.aclose()

    except ConnectionClosed:
        assert True

async def test_multisymbol():
    await sleep(random())
    try:
        messages = connect('testnet', ['XBTUSD', 'ETHUSD'], None, os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET'))
        count = 0
        ws = await messages.asend(None)
        async for msg in messages:
            assert isinstance(msg, dict)
            count += 1
            if count >= 10:
                print(count)
                await ws.aclose()
    except ConnectionClosed:
        assert True

async def test_context_manager():
    async with BitMEXWebsocket.connect('testnet', ['XBTUSD', 'ETHUSD'], ['instrument'], os.getenv('TESTNET_API_KEY'), os.getenv('TESTNET_API_SECRET')) as bitmex_ws:
        count = 0
        async for msg in bitmex_ws.listen('instrument'):
            count += 1
            print(count)
            if count >= 10:
                break
        assert True
