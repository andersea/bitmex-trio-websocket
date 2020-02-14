import os
import sys
import logging

sys.path.append(os.getcwd() + '/..')

import trio
from async_generator import aclosing

from bitmex_trio_websocket import open_bitmex_websocket

logging.basicConfig(level='INFO', format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')

async def main():
    async with open_bitmex_websocket('testnet') as bws:
        count = 0
        async with aclosing(bws.listen('orderBookL2', 'XBTUSD')) as agen:
            async for msg in agen:
                print(f'Received message, symbol: \'{msg["symbol"]}\'')
                count += 1
                if count == 100:
                    break


if __name__ == '__main__':
    trio.run(main)