# -*- coding: utf-8 -*-

"""BitMEX Websocket Connection."""
import logging

from trio_websocket import connect_websocket_url, ConnectionClosed
from ujson import loads

from .auth import generate_expires, generate_signature

log = logging.getLogger(__name__)

async def connect(nursery, network, api_key=None, api_secret=None):
    """Start a BitMEX websocket connection."""
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

        log.debug('Opening websocket.')
        ws = await connect_websocket_url(nursery, url, extra_headers=headers)
        # Yields the websocket itself as the first value, so outsiders can access it.
        yield ws
        while True:
            log.debug('Getting next raw message from websocket.')
            raw_message = await ws.get_message()
            log.debug('->')
            log.debug(raw_message)
            log.debug('-|')
            message = loads(raw_message)
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
            else:
                log.warning('Received unknown message type: %s', message)

    except OSError as ose:
        log.error('Connection attempt failed: %s', type(ose).__name__)
    except ConnectionClosed as cle:
        log.info('Connection closed. Closed reason: %s', cle.reason)
