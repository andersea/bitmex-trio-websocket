from collections import defaultdict
from datetime import datetime, timezone
import decimal
import logging
import typing

from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)

class Storage:

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self):
        self.data = defaultdict(SortedDict)
        # Special storage for orderBookL2
        # dict[symbol][side][id]
        self.orderbook = defaultdict(lambda: defaultdict(SortedDict))
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

            if table not in self.keys:
                self.keys[table] = []

            # There are four possible actions from the WS:
            # 'partial' - full table image
            # 'insert'  - new row
            # 'update'  - update row
            # 'delete'  - delete row
            if action == 'partial':
                logger.debug('%s: partial', table)
                # Keys are communicated on partials to let you know how to uniquely identify
                # an item. We use it for updates.
                self.keys[table] = message['keys']

                if table =='orderBookL2':
                    # This is used to yield the output. Not sure if only a single symbol
                    # is included per partial. If so, then finding unique symbols is
                    # obviously a waste of time.
                    symbols = set()
                    for item in message['data']:
                        symbols.add(item['symbol'])
                        self.orderbook[item['symbol']][item['side']][item['id']] = item
                    # Yield order book per symbol in the partial.
                    for symbol in symbols:
                        yield (self.orderbook[symbol], symbol, table, action)
                else:
                    for item in message['data']:
                        # Store item by key
                        self.data[table][self.make_key(table, item)] = item
                        if 'symbol' in item:
                            yield (item, item['symbol'], table, action)
                        else:
                            yield (item, None, table, action)

            elif action == 'insert':
                logger.debug('%s: inserting %s', table, message["data"])

                # Limit the max length of the table to avoid excessive memory usage.
                if table == 'order':
                    # Trim closed orders that are older than a minute - Filled orders
                    # can be reopened by amending leavesQty within a minute. After that
                    # we can delete them.
                    outdated_keys = [
                        k for k, i in self.data[table].items()
                        if i['leavesQty'] <= 0 and (datetime.now(timezone.utc) - parse_timestamp(i['timestamp'])).total_seconds() > 60
                    ]
                    for key in outdated_keys:
                        del self.data[table][key]
                elif table == 'orderBookL2':
                    # Don't trim the order book because we'll lose valuable state if we do.
                    pass
                elif len(self.data[table]) > self.MAX_TABLE_LEN:
                    # Delete the first half of the keys
                    del self.data[table].keys()[:(self.MAX_TABLE_LEN // 2)]

                # Insert items
                if table == 'orderBookL2':
                    for item in message['data']:
                        self.orderbook[item['symbol']][item['side']][item['id']] = item
                        yield (item, item['symbol'], table, action)
                else:
                    for item in message['data']:
                        self.data[table][self.make_key(table, item)] = item
                        if 'symbol' in item:
                            yield (item, item['symbol'], table, action)
                        else:
                            yield (item, None, table, action)


            elif action == 'update':
                logger.debug('%s: updating %s', table, message["data"])
                for update in message['data']:
                    try:
                        if table == 'orderBookL2':
                            item = self.orderbook[update['symbol']][update['side']][update['id']]
                        else:
                            item = self.data[table][self.make_key(table, update)]

                        # Update this item.
                        item.update(update)

                        # Send back the updated item
                        if 'symbol' in item:
                            yield (item, item['symbol'], table, action)
                        else:
                            yield (item, None, table, action)
                    except KeyError:
                        continue # No item found to update. Could happen before push

            elif action == 'delete':
                logger.debug('%s: deleting %s', table, message["data"])
                for deleted in message['data']:
                    # Locate the item in the collection and remove it.
                    try:
                        if table == 'orderBookL2':
                            del self.orderbook[deleted['symbol']][deleted['side']][deleted['id']]
                        else:
                            del self.data[table][self.make_key(table, deleteData)]
                    except KeyError:
                        pass # Item not found
            else:
                raise Exception("Unknown action: %s" % action)

            logger.debug('Next iteration.')
    
    def make_key(self, table, match_data):
        return tuple(match_data[key] for key in self.keys[table])
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> datetime:
        return datetime(timestamp.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S.%f%z')
