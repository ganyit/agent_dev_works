import asyncio

async def fetch(n: int) -> int:
    await asyncio.sleep(1)
    print ("haiii");
    return n

#async def main() -> None:
    a = await fetch(1)   # waits 1s
    b = await fetch(2)   # then another 1s
    c = await fetch(3)   # then another 1s
    # total: ~3 seconds — no concurrency gained!



async def main() -> None:
    results = await asyncio.gather(
        fetch(1), fetch(2), fetch(3)
    )
asyncio.run(main())

import asyncio
import httpx

async def fetch(client, url, sem):
    async with sem:                         # bouncer: only 10 past this point
        return await client.get(url)

async def main(urls):
    sem = asyncio.Semaphore(10)             # set the limit to 10
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, u, sem) for u in urls]
        return await asyncio.gather(*tasks) # still gather ALL of them...
                                            # ...but the semaphore keeps only 10 active

asyncio.run(main(["https://httpbin.org/json"] * 1000))