from datetime import datetime, timezone
import decimal
import logging
import typing

logger = logging.getLogger(__name__)

class Storage:

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self):
        self.data = {}
        self.keys = {}

    async def process(self, ws):
        # Yields the connection itself for outsiders.
        yield await ws.asend(None)
        # Processes the rest of the messages
        logger.debug('First iteration.')
        async for message in ws:

            table = message['table'] if 'table' in message else None
            action = message['action'] if 'action' in message else None

            logger.debug('Received %s message for table %s.', action, table)

            if table not in self.data:
                self.data[table] = []

            if table not in self.keys:
                self.keys[table] = []

            # There are four possible actions from the WS:
            # 'partial' - full table image
            # 'insert'  - new row
            # 'update'  - update row
            # 'delete'  - delete row
            if action == 'partial':
                logger.debug('%s: partial', table)
                self.data[table] += message['data']
                # Keys are communicated on partials to let you know how to uniquely identify
                # an item. We use it for updates.
                self.keys[table] = message['keys']

                for item in message['data']:
                    if 'symbol' in item:
                        yield (item, item['symbol'], table, action)
                    else:
                        yield (item, None, table, action)

            elif action == 'insert':
                logger.debug('%s: inserting %s', table, message["data"])
                self.data[table] += message['data']

                # Limit the max length of the table to avoid excessive memory usage.
                if table == 'order':
                    # Trim closed orders that are older than a minute - Filled orders
                    # can be reopened by amending leavesQty within a minute. After that
                    # we can delete them.
                    self.data[table] = [
                        i for i in self.data[table]
                        if i['leavesQty'] <= 0 and (datetime.now(timezone.utc) - parse_timestamp(i['timestamp'])).total_seconds() > 60
                    ]
                elif table == 'orderBookL2':
                    # Don't trim the order book because we'll lose valuable state if we do.
                    pass
                elif len(self.data[table]) > self.MAX_TABLE_LEN:
                    self.data[table] = self.data[table][(self.MAX_TABLE_LEN // 2):]

                for item in message['data']:
                    if 'symbol' in item:
                        yield (item, item['symbol'], table, action)
                    else:
                        yield (item, None, table, action)

            elif action == 'update':
                logger.debug('%s: updating %s', table, message["data"])
                # Locate the item in the collection and update it.
                for updateData in message['data']:
                    item = self.find_item(table, updateData)
                    if not item:
                        continue  # No item found to update. Could happen before push

                    # Update this item.
                    item.update(updateData)

                    # Send back the updated item
                    if 'symbol' in item:
                        yield (item, item['symbol'], table, action)
                    else:
                        yield (item, None, table, action)

            elif action == 'delete':
                logger.debug('%s: deleting %s', table, message["data"])
                # Locate the item in the collection and remove it.
                for deleteData in message['data']:
                    item = self.find_item(table, deleteData)
                    self.data[table].remove(item)
            else:
                raise Exception("Unknown action: %s" % action)

            logger.debug('Next iteration.')

    def get_instrument(self, symbol):
        instruments = self.data['instrument']
        matchingInstruments = [i for i in instruments if i['symbol'] == symbol]
        if not matchingInstruments:
            raise Exception("Unable to find instrument or index with symbol: " + symbol)
        instrument = matchingInstruments[0]
        # Turn the 'tickSize' into 'tickLog' for use in rounding
        # http://stackoverflow.com/a/6190291/832202
        instrument['tickLog'] = decimal.Decimal(str(instrument['tickSize'])).as_tuple().exponent * -1
        return instrument

    def find_item(self, table: str, match_data: typing.Mapping[str, typing.Union[str, int, float]):
        keys = self.keys[table]
        records = self.data[table]
        for item in records:
            matched = True
            for key in keys:
                if item[key] != match_data[key]:
                    matched = False
            if matched:
                return item
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> datetime:
        return datetime(timestamp.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S.%f%z')
