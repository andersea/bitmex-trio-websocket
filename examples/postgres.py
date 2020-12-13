import os

from async_generator import aclosing
import trio

from bitmex_trio_websocket import open_bitmex_websocket, PostgresStorage

async def test():
    async with open_bitmex_websocket(
        'testnet',
        os.getenv('TESTNET_API_KEY'),
        os.getenv('TESTNET_API_SECRET'),
        storage=PostgresStorage(os.getenv('POSTGRESQL'))
    ) as ws:
        async with aclosing(ws.listen('instrument')) as aiter:
            async for item in aiter:
                print(item)

if __name__ == '__main__':
    trio.run(test)