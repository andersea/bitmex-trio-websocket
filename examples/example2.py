import os
import sys
import logging

sys.path.append(os.getcwd() + '/..')

import trio
from async_generator import aclosing

from bitmex_trio_websocket import open_bitmex_websocket

logging.basicConfig(level='INFO', format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')


async def instrument(websocket, symbol):
    async with aclosing(websocket.listen('instrument', symbol)) as agen:
        async for i in agen:
            print(i)

async def main():
    with trio.move_on_after(10):
        async with open_bitmex_websocket('testnet') as bws, trio.open_nursery() as nursery:
            # Only one subscription is added. Both listeners get messages from the same channel.
            nursery.start_soon(instrument, bws, 'XRPUSD')
            nursery.start_soon(instrument, bws, 'XRPUSD')


if __name__ == '__main__':
    trio.run(main)