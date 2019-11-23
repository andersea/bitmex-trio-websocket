import logging
import decimal

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
        # Processes the rest of the messages messages
        async for message in ws:

            table = message['table'] if 'table' in message else None
            action = message['action'] if 'action' in message else None

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
                # Don't trim orders because we'll lose valuable state if we do.
                if table not in ['order', 'orderBookL2'] and len(self.data[table]) > self.MAX_TABLE_LEN:
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
                    item = findItemByKeys(self.keys[table], self.data[table], updateData)
                    if not item:
                        continue  # No item found to update. Could happen before push

                    # Log executions
                    if table == 'order':
                        is_canceled = 'ordStatus' in updateData and updateData['ordStatus'] == 'Canceled'
                        if 'cumQty' in updateData and not is_canceled:
                            contExecuted = updateData['cumQty'] - item['cumQty']
                            if contExecuted > 0:
                                instrument = self.get_instrument(item['symbol'])
                                logger.info('Execution: %s %d Contracts of %s at %.*f',
                                            item["side"], contExecuted, item["symbol"],
                                            instrument["tickLog"], item["price"])

                    # Update this item.
                    item.update(updateData)

                    # Remove canceled / filled orders
                    if table == 'order' and item['leavesQty'] <= 0:
                        self.data[table].remove(item)

                    # Send back the updated item
                    if 'symbol' in item:
                        yield (item, item['symbol'], table, action)
                    else:
                        yield (item, None, table, action)

            elif action == 'delete':
                logger.debug('%s: deleting %s', table, message["data"])
                # Locate the item in the collection and remove it.
                for deleteData in message['data']:
                    item = findItemByKeys(self.keys[table], self.data[table], deleteData)
                    self.data[table].remove(item)
            else:
                raise Exception("Unknown action: %s" % action)

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

def findItemByKeys(keys, table, matchData):
    for item in table:
        matched = True
        for key in keys:
            if item[key] != matchData[key]:
                matched = False
        if matched:
            return item
