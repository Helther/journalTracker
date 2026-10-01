import asyncio
import logging
import sys

from app.db.config import DBConfig
from app.db.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="[bootstrap] %(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("bootstrap")

async def _init_db() -> None:
    async with Database(DBConfig()) as db:
        await db.init()

async def wait_for_db(
    retries: int = 30,
    delay: float = 2.0,
) -> None:
    async with Database(DBConfig()) as db:
        for attempt in range(1, retries + 1):
            try:
                await db.healthcheck()
                log.info("Database is queryable.")
                return
            except Exception as e:
                log.warning("attempt %s/%s failed: %s", attempt, retries, e)
                await asyncio.sleep(delay)

        raise RuntimeError("Database not reachable")

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(wait_for_db()) 
    except KeyboardInterrupt:
        log.info("Interrupted during DB bootstrap.")
        sys.exit(130)
    try:
        asyncio.run(_init_db())      
    except KeyboardInterrupt:
        log.info("Interrupted during DB init.")
        sys.exit(130)


if __name__ == "__main__":
    main()
