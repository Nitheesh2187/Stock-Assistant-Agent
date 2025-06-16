import asyncio

async def run_async_task(coro):
    return await coro

def run_in_loop(coro):
    try:
        return asyncio.get_running_loop().run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)