import asyncio
import os

import httpx

LB_URL = os.getenv("LB_URL", "http://127.0.0.1:8000")
URL = f"{LB_URL}/health"
TOTAL_REQUESTS = 100_000
BATCH_SIZE = 500
SLEEP_BETWEEN_BATCHES = 0.5


async def fetch(client, idx):
    try:
        response = await client.get(URL, timeout=5.0)
        data = response.json()
        return {"idx": idx, "status": "ok", "service": data.get("service")}
    except Exception as e:
        return {"idx": idx, "status": "error", "error": str(e)}


async def run_load_test():
    async with httpx.AsyncClient() as client:
        for start in range(0, TOTAL_REQUESTS, BATCH_SIZE):
            batch_tasks = [
                fetch(client, i) for i in range(start, min(start + BATCH_SIZE, TOTAL_REQUESTS))
            ]
            results = await asyncio.gather(*batch_tasks)

            for res in results:
                if res["status"] == "error":
                    print(res)

            await asyncio.sleep(SLEEP_BETWEEN_BATCHES)


if __name__ == "__main__":
    asyncio.run(run_load_test())
