import logging

from async_generator import aclosing
from slurry.sections.abc import Section

log = logging.getLogger(__name__)

class Parser(Section):
    async def pump(self, input, output):
        async for message in input:
            if 'info' in message:
                log.debug('Connected to BitMEX realtime api.')
            elif 'subscribe' in message:
                if message['success']:
                    log.debug('Subscribed to %s.', message["subscribe"])
                else:
                    log.error('Unable to subscribe to %s. Error: "%s" Please check and restart.',
                                message["request"]["args"][0], message["error"])
            elif 'action' in message:
                await output(message)
            elif 'request' in message and 'op' in message['request'] and message['request']['op'] == 'cancelAllAfter':
                log.debug('Dead mans switch reset. All open orders will be cancelled at %s.', message['cancelTime'])
            elif 'error' in message:
                log.error('%s - Request: %s', message['error'], message['request'])
            else:
                log.warning('Received unknown message type: %s', message)
