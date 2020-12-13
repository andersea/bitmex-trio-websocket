import logging

from slurry import Section

log = logging.getLogger(__name__)

class Logger(Section):

    async def pump(self, input, output):
        async for item in input:
            log.debug(item)
            await output.send(item)
