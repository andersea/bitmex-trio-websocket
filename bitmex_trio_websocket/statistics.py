import logging

from slurry import Section

log = logging.getLogger(__name__)

class Statistics(Section):

    async def pump(self, input, output):
        async for message in input:
            if message['data'] and 'symbol' in message['data'][0]:
                symbols = set(record['symbol'] for record in message['data'])
            else:
                symbols = []

            log.info('%s %d record%s in "%s" - %d unique symbol%s %s',
                     message['action'].capitalize(), len(message['data']), 
                     '' if len(message['data']) == 1 else 's',
                     message['table'].lower(),
                     len(symbols), '' if len(symbols) == 1 else 's', ','.join(symbols))
            