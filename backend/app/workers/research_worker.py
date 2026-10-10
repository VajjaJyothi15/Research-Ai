import asyncio
from app.core.logging import logger


async def run_worker():
    logger.info("ResAI Async Research Job Worker started.")
    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(run_worker())
