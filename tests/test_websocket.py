#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `bitmex_trio_websocket.websocket` module."""

import trio
from bitmex_trio_websocket.websocket import connect
from async_generator import async_generator


async def test_endpoint_argument():
    async with trio.open_nursery() as nursery:
        cn = connect(nursery, 'mainnet')
        assert getattr(cn, '__aiter__', None) is not None
        cn = connect(nursery, 'testnet')
        assert getattr(cn, '__aiter__', None) is not None
        try:
            connect(nursery, 'incorrect')
        except Exception as e:
            assert isinstance(e, ValueError)
