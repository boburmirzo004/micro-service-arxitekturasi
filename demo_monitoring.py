import asyncio
import os

import httpx

LB_URL = os.getenv("LB_URL", "http://127.0.0.1:8000")
STATS_URL = f"{LB_URL}/stats"
NUM_REQUESTS = 1000

LIMITS = httpx.Limits(max_connections=1200, max_keepalive_connections=200)


async def sorovlar_yuborish():
    print(f"{NUM_REQUESTS} ta sorov yuborilmoqda...")
    async with httpx.AsyncClient(limits=LIMITS, timeout=30.0) as client:
        tasks = [client.get(LB_URL) for _ in range(NUM_REQUESTS)]
        natijalar = await asyncio.gather(*tasks, return_exceptions=True)
        xatolar = [r for r in natijalar if isinstance(r, Exception)]
        if xatolar:
            print(f"{len(xatolar)} ta sorovda xatolik.", flush=True)


async def monitoring():
    print("Load Balancer Monitoring")
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(10):
            try:
                response = await client.get(STATS_URL)
                if response.status_code == 200:
                    data = response.json()
                    active = data["details"]["active_connections"]
                    metrics = data.get("metrics", {})
                    print(
                        f"Vaqt: {i*0.5:.1f}s | "
                        f"Active: {active} | "
                        f"Total: {metrics.get('total_requests')} | "
                        f"Errors: {metrics.get('total_errors')} | "
                        f"Avg: {metrics.get('avg_latency_sec')}"
                    )
            except Exception:
                pass
            await asyncio.sleep(0.5)


async def main():
    print("Demo boshlanmoqda...")
    print(f"{NUM_REQUESTS} ta sorov yuborib real vaqtda yukni koramiz.\n")

    monitor_task = asyncio.create_task(monitoring())
    await asyncio.sleep(0.5)
    request_task = asyncio.create_task(sorovlar_yuborish())

    await asyncio.gather(monitor_task, request_task)
    print("\nDemo yakunlandi.")


if __name__ == "__main__":
    asyncio.run(main())
