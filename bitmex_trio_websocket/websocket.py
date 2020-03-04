# -*- coding: utf-8 -*-

"""BitMEX Websocket Connection."""
from collections import defaultdict
import logging
from typing import Optional

from async_generator import aclosing, asynccontextmanager
import trio
from trio_websocket import connect_websocket_url, ConnectionClosed, WebSocketConnection
import ujson

from .auth import generate_expires, generate_signature
from .storage import Storage

log = logging.getLogger(__name__)

class BitMEXWebsocket:
    def __init__(self):
        self.storage = Storage()
        self._ws = None
        self._listeners = defaultdict(list)
        self._listeners_attached = trio.Event()
        self._subscriptions = set()
    
    async def listen(self, table: str, symbol: Optional[str]=None):
        """
        Subscribe to a channel and optionally a specific symbol.
        
        Returns an async generator that yields messages from the subscribed channel.
        """
        send_channel, receive_channel = trio.open_memory_channel(0)
        listener = (table, symbol)
        self._listeners[listener].append(send_channel)
        if listener not in self._subscriptions:
            self._subscriptions.add(listener)
            topic = table if not symbol else f'{table}:{symbol}'
            await self._ws.send_message(ujson.dumps({'op': 'subscribe', 'args': [topic]}))
        self._listeners_attached.set()
        try:
            while True:
                yield await receive_channel.receive()
        finally:
            log.debug('Listener detached from table: %s, symbol: %s', table, symbol)
            self._listeners[listener].remove(send_channel)

    @asynccontextmanager
    async def _connect(self, network, api_key, api_secret, dead_mans_switch):
        """Open a BitMEX websocket connection."""
        try:
            if network == 'mainnet':
                url = 'wss://www.bitmex.com/realtime'
            else:
                url = 'wss://testnet.bitmex.com/realtime'

            log.debug('Generating authentication headers.')
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            headers = None
            if api_key and api_secret:
                nonce = generate_expires()
                headers = [
                    ('api-expires', str(nonce)),
                    ('api-signature', generate_signature(api_secret, 'GET', '/realtime', nonce, '')),
                    ('api-key', api_key)
                ]

            async with trio.open_nursery() as nursery:
                log.debug('Opening websocket connection.')
                self._ws = await connect_websocket_url(nursery, url, extra_headers=headers)
                if dead_mans_switch:
                    nursery.start_soon(self._dead_mans_switch)
                nursery.start_soon(self._run)
                yield self
                log.debug('BitMEXWebsocket context exit. Cancelling running tasks.')
                nursery.cancel_scope.cancel()
            log.debug('BitMEXWebsocket closed.')

        except OSError as ose:
            log.error('Connection attempt failed: %s', type(ose).__name__)

    async def _run(self):
        """Process each message through the storage engine and broadcast the result to listeners."""
        log.debug('Run task starting.')
        await self._listeners_attached.wait()
        try:
            async with aclosing(self.storage.process(self._websocket_parser())) as agen:
                async for item, item_symbol, item_table, _ in agen:
                    # Lock list of listeners while sending
                    listeners_for_table = [key for key in self._listeners.keys() if item_table == key[0]]
                    for listen_table, listen_symbol in listeners_for_table:
                        if item_symbol:
                            if not listen_symbol or listen_symbol == item_symbol:
                                for send_channel in self._listeners[(listen_table, listen_symbol)]:
                                    await send_channel.send(item)
                        else:
                            for send_channel in self._listeners[(listen_table, listen_symbol)]:
                                await send_channel.send(item)
        finally:
            log.debug('Run task done.')

    async def _dead_mans_switch(self):
        log.debug('Dead mans switch task starting.')
        op = ujson.dumps({'op': 'cancelAllAfter', 'args': 60000})
        while True:
            await self._ws.send_message(op)
            await trio.sleep(15)

    async def _websocket_parser(self):
        try:
            while True:
                log.debug('Getting next raw message from websocket.')
                raw_message = await self._ws.get_message()
                log.debug('->')
                log.debug(raw_message)
                log.debug('-|')
                message = ujson.loads(raw_message)
                if 'info' in message:
                    log.debug('Connected to BitMEX realtime api.')
                elif 'subscribe' in message:
                    if message['success']:
                        log.debug('Subscribed to %s.', message["subscribe"])
                    else:
                        log.error('Unable to subscribe to %s. Error: "%s" Please check and restart.',
                                    message["request"]["args"][0], message["error"])
                elif 'action' in message:
                    yield message
                elif 'request' in message and 'op' in message['request'] and message['request']['op'] == 'cancelAllAfter':
                    log.debug('Dead mans switch reset. All open orders will be cancelled at %s.', message['cancelTime'])
                else:
                    log.warning('Received unknown message type: %s', message)

        except ConnectionClosed as cle:
            log.info('Connection closed. Closed reason: %s', cle.reason)

@asynccontextmanager
async def open_bitmex_websocket(network: str, api_key: str=None, api_secret: str=None, *, dead_mans_switch=False):
    """Open a new BitMEX websocket connection context."""
    if network not in ('mainnet', 'testnet'):
        raise ValueError('network argument must be either \'mainnet\' or \'testnet\'')
    
    bitmex_websocket = BitMEXWebsocket()
    #pylint: disable=not-async-context-manager
    async with bitmex_websocket._connect(network, api_key, api_secret, dead_mans_switch): 
        yield bitmex_websocket
