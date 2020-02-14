from collections import defaultdict
from datetime import datetime, timezone
import decimal
import logging
from typing import Mapping, Union, Iterable

# Type alias for a table record
TableItem = Mapping[str, Union[int, float, str]]

from async_generator import aclosing
from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)

class Storage:
    """
    This is a async sans io storage engine for the BitMEX websocket api.
    """

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self):
        self.data = defaultdict(SortedDict)
        # Special storage for orderBookL2
        # dict[symbol][side][id]
        self.data['orderBookL2'] = defaultdict(lambda: defaultdict(SortedDict))
        self.keys = {}

    async def process(self, messages):
        """Updates the storage from parsed websocket messages"""
        async with aclosing(messages) as agen:
            async for message in agen:
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
                    # an item. Some tables don't have keys. For those, we can use the attributes
                    # field to generate a key.
                    if message['keys']:
                        self.keys[table] = message['keys']
                    else:
                        self.keys[table] = list(message['attributes'].keys())

                    # Insert data
                    self.insert(table, message['data'])
                    # Generate inserted items
                    if table =='orderBookL2':
                        # For the orderBook we send the complete book, since sending each item
                        # in turn doesn't make much sense, for such a big table.
                        symbol = message['data'][0]['symbol']
                        yield (self.data[table][symbol], symbol, table, action)
                    else:
                        # For all other tables, generate each individual item
                        for item in message['data']:
                            if 'symbol' in item:
                                yield (item, item['symbol'], table, action)
                            else:
                                yield (item, None, table, action)

                elif action == 'insert':
                    logger.debug('%s: inserting %s', table, message["data"])

                    # Check if table length exceeded
                    self._limit_table_size(table)
                    # Insert items
                    self.insert(table, message['data'])
                    # Generate inserted items
                    for item in message['data']:
                        if 'symbol' in item:
                            yield (item, item['symbol'], table, action)
                        else:
                            yield (item, None, table, action)


                elif action == 'update':
                    logger.debug('%s: updating %s', table, message["data"])
                    for update in message['data']:
                        try:
                            if table == 'orderBookL2':
                                item = self.data[table][update['symbol']][update['side']][update['id']]
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
                    for item in message['data']:
                        # Locate the item in the collection and remove it.
                        try:
                            if table == 'orderBookL2':
                                del self.data[table][item['symbol']][item['side']][item['id']]
                            else:
                                del self.data[table][self.make_key(table, item)]
                        except KeyError:
                            pass # Item not found
                    # Send back the deletion fragment
                    for item in message['data']:
                        if 'symbol' in item:
                            yield (item, item['symbol'], table, action)
                        else:
                            yield (item, None, table, action)

                else:
                    raise Exception(f'Unknown action: {action}')
    
    def _limit_table_size(self, table):
        """Limit the max length of the table to avoid excessive memory usage."""
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
    
    def insert(self, table: str, data: Iterable[TableItem]):
        """Inserts a sequence of table items into the given table"""
        if table == 'orderBookL2':
            if len(set(item['symbol'] for item in data)) != 1:
                raise RuntimeError('Order book update contained multiple symbols')
            for item in data:
                self.data[table][item['symbol']][item['side']][item['id']] = item
        else:
            self.data[table].update((self.make_key(table, item), item) for item in data)
    
    def make_key(self, table: str, match_data: TableItem) -> tuple:
        """Creates a storage key tuple from a table item"""
        if table == 'orderBookL2':
            raise ValueError('orderBookL2 must be indexed by [symbol][side][id]')
        return tuple(match_data[key] for key in self.keys[table])
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> datetime:
        """Parses a BitMEX timestamp into a datetime object"""
        return datetime(timestamp.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S.%f%z')
