# -*- coding: utf-8 -*-

"""BitMEX Websocket Connection."""
import logging

from trio_websocket import open_websocket_url
from ujson import loads

from .auth import generate_expires, generate_signature

logger = logging.getLogger(__name__)

async def connect(endpoint, symbol=None, api_key=None, api_secret=None):
    """Start a BitMEX websocket connection."""
    try:
        if endpoint == 'mainnet':
            url = 'wss://www.bitmex.com/realtime'
        else:
            url = 'wss://testnet.bitmex.com/realtime'

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        subscriptions = []
        if symbol:
            if isinstance(symbol, str):
                symbol = [symbol]
            for s in symbol:
                subscriptions += [sub + ':' + s for sub in ['instrument', 'quote', 'trade', 'tradeBin1m']]
        if api_key and api_secret:
            subscriptions += ['margin', 'position', 'order', 'execution']
        url += '?subscribe=' + ','.join(subscriptions)

        logger.debug('Generating authentication headers.')
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

        logger.debug('Opening websocket.')
        async with open_websocket_url(url, extra_headers=headers) as ws:
            # Yields the websocket itself as the first value, so outsiders can access it.
            yield ws
            while True:
                message = loads(await ws.get_message())
                if 'info' in message:
                    logger.debug('Connected to BitMEX realtime api.')
                elif 'subscribe' in message:
                    if message['success']:
                        logger.debug('Subscribed to %s.', message["subscribe"])
                    else:
                        logger.error('Unable to subscribe to %s. Error: "%s" Please check and restart.',
                                     message["request"]["args"][0], message["error"])
                elif 'action' in message:
                    yield message
                else:
                    logger.warning('Received unknown message type: %s', message)
    except OSError as ose:
        logger.error('Connection attempt failed: %s', type(ose).__name__)
