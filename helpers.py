# helpers.py
import asyncio
import random

async def with_retries(coro, *args, retries=3, backoff=2, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            return await coro(*args, **kwargs)

        except Exception as e:
            if attempt == retries:
                raise
            wait = backoff ** attempt + random.random()
            print(f"⚠️ Error: {e} — retrying in {wait:.1f}s…")
            await asyncio.sleep(wait)

