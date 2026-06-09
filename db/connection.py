import asyncpg
import logging
import os
from bot.config import DATABASE_URL

logger = logging.getLogger(__name__)

_MIGRATIONS_FILE = os.path.join(os.path.dirname(__file__), "migrations", "001_init.sql")


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                max_inactive_connection_lifetime=300,
                command_timeout=30,
            )
            logger.info("Database connection pool created.")
            await self._run_migrations()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def _run_migrations(self):
        try:
            with open(_MIGRATIONS_FILE, "r") as f:
                sql = f.read()
            async with self.pool.acquire() as conn:
                await conn.execute(sql)
            logger.info("Migrations applied.")
        except Exception as e:
            logger.error(f"Migration error: {e}")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed.")

    async def execute(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def fetchval(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchval(query, *args)

db = Database()
