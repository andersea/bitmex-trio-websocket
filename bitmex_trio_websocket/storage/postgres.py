import logging
from typing import final

import pendulum
from slurry import Section
from trio_asyncio import open_loop
import triopg

log = logging.getLogger(__name__)

class PostgresStorage(Section):
    def __init__(self, url, schema='bitmex') -> None:
        self.url = url
        self.schema = schema
        self.keys = {}

    async def pump(self, input, output) -> None:
        try:
            async with open_loop(), triopg.connect(self.url) as conn:
                await conn.set_type_codec(
                    'uuid', schema='pg_catalog',
                    encoder=lambda d: d,
                    decoder=lambda d: d)
                await conn.set_type_codec(
                    'timestamptz', schema='pg_catalog',
                    encoder=lambda d: d,
                    decoder=pendulum.parse)
                postgres = PostgresUtils(conn, self.schema)
                async for message in input:
                    action = message['action']
                    table = message['table'].lower()

                    if action == 'partial':
                        if await postgres.table_exists(table):
                            # if 'filter' in message:
                            #     await postgres.truncate(table)
                            pass
                        else:
                            await postgres.create_table(table, message)
                        self.keys[table] = message['keys']
                        if message['data']:
                            await postgres.upsert(table, self.keys[table], message['data'])
                    if action == 'insert':
                        await postgres.insert(table, message['data'])
                    if action == 'update':
                        await postgres.update(table, self.keys[table], message['data'])
                    if action == 'delete':
                        await postgres.delete(table, message['data'])
                    for item in message['data']:
                        if 'symbol' in item:
                            await output((item, item['symbol'], table, action))
                        else:
                            await output((item, None, table, action))
        finally:
            log.debug('Postgres storage engine exit.')            

class PostgresUtils:
    def __init__(self, conn, schema) -> None:
        self.conn = conn
        self.schema = schema
    
    async def table_exists(self, table):
        return await self.conn.fetchval(f'SELECT to_regclass($1)', self.schema + '.' + table) is not None

    async def create_table(self, table, message):
        translate_types = {
            'long': 'int8',
            'float': 'double precision',
            'symbol': 'text',
            'string': 'text',
            'timestamp': 'timestamptz',
            'timespan': 'timestamptz',
            'boolean': 'boolean',
            'guid': 'uuid',
        }
        keys = message['keys']
        if not keys:
            first_column = next(iter(message['types'].items()))
            if first_column[1] == 'guid':
                keys = [first_column[0]]

        def constraints(col):
            if col in message['keys'] or col in message['attributes']:
                return " NOT NULL"
            return " NULL"
            
        sql = []

        sql.append(f'CREATE TABLE "{self.schema}"."{table}" (')
        sql.append(",".join(
            f'"{col}" {translate_types[typ]}{constraints(col)}'
            for col, typ in message['types'].items()
        ))
        if keys:
            sql.append(f', PRIMARY KEY ({",".join(f"""{col}""" for col in keys)})')
        sql.append(');')
        for col in (col for col, typ in message['attributes'].items() if typ == 'sorted'):
            sql.append(f'CREATE INDEX ON "{self.schema}"."{table}" ("{col}");')

        await self.conn.execute("".join(sql))
    
    # async def truncate(self, table):
    #     await self.conn.execute(f'TRUNCATE TABLE "{self.schema}"."{table}"')

    async def insert(self, table, data):
        await self.conn.executemany(f'''
        INSERT INTO "{self.schema}"."{table}"
        VALUES ({f','.join(f'${i+1}' for i in range(len(data[0])))})
        ''', [tuple(record.values()) for record in data])

    async def upsert(self, table, keys, data):
        await self.conn.executemany(f'''
        INSERT INTO "{self.schema}"."{table}"
        VALUES ({f','.join(f'${i+1}' for i in range(len(data[0])))})
        ON CONFLICT ON CONSTRAINT "{table}_pkey" DO UPDATE
        SET ({','.join(f'"{col}"' for col in data[0].keys())}) = ({','.join(f'${i+1}' for i in range(len(data[0])))})
        WHERE {' and '.join(f'"{table}"."{key}" = ${i+1}' for i, key in enumerate(keys))}
        ''', [tuple(record.values()) for record in data])

    async def update(self, table, keys, data):
        for record in data:
            await self.conn.execute(f'''
            UPDATE "{self.schema}"."{table}"
            SET ({','.join(f'"{col}"' for col in record.keys())}) = ({','.join(f'${i+1}' for i in range(len(record)))})
            WHERE {' and '.join(f'"{table}"."{key}" = ${i+1}' for i, key in enumerate(keys))}
            ''',*record.values())
    
    async def delete(self, table, data):
        await self.conn.executemany(f'''
        DELETE FROM "{self.schema}"."{table}"
        WHERE {' and '.join(f'"{table}"."{key}" = ${i+1}' for i, key in enumerate(data[0].keys()))}
        ''', [tuple(record.values()) for record in data])
