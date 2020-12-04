import trio
from bitmex_trio_websocket.postgres import PostgresStorage
from bitmex_trio_websocket.websocket import open_bitmex_websocket
import os

from async_generator import aclosing
import pytest

@pytest.fixture
async def testnet_websocket():
    async with open_bitmex_websocket(
        'testnet',
        # os.getenv('TESTNET_API_KEY'),
        # os.getenv('TESTNET_API_SECRET'),
        # storage=PostgresStorage(os.getenv('POSTGRESQL'))
    ) as ws:
        yield ws

async def test_storage(testnet_websocket):
    async with aclosing(testnet_websocket.listen('funding')) as aiter:
        async for funding in aiter:
            assert 'symbol' in funding
            break