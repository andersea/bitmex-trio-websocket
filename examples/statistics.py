import os

from async_generator import aclosing
import trio

from bitmex_trio_websocket import open_bitmex_websocket, Statistics

from examples._logging import log

async def main():
    async with open_bitmex_websocket(
        'testnet',
        os.getenv('TESTNET_API_KEY'),
        os.getenv('TESTNET_API_SECRET'),
        storage=Statistics()
    ) as ws:
        async with aclosing(ws.listen('tradeBin1m')) as aiter:
            async for item in aiter:
                print(item)

if __name__ == '__main__':
    trio.run(main)