from async_generator import aclosing
from slurry import Section
from trio_asyncio import open_loop
import triopg

class PostgresStorage(Section):
    def __init__(self, url, schema='bitmex') -> None:
        self.url = url
        self.schema = schema

    async def pump(self, input, output) -> None:
        async with open_loop(), triopg.connect(self.url) as conn, aclosing(input) as aiter:
            tables = [r[0] for r in await conn.fetch(
                'SELECT table_name FROM information_schema."tables" t '
                'WHERE table_schema = \'bitmex\'')
            ]
            async for message in aiter:
                print(message)
                pass

