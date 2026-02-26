import asyncio
import httpx
import json
import time

LB_URL = "http://127.0.0.1:8000"
STATS_URL = f"{LB_URL}/stats"
NUM_REQUESTS = 50

async def send_requests():
    """Sends many requests to the load balancer to create load"""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(LB_URL) for _ in range(NUM_REQUESTS)]
        await asyncio.gather(*tasks)

async def monitor_stats():
    """Monitors the load balancer stats while load is being applied"""
    print("--- 🔍 Load Balancer Monitoring ---")
    async with httpx.AsyncClient() as client:
        for i in range(5): # Check stats 5 times
            try:
                response = await client.get(STATS_URL)
                data = response.json()
                active = data['details']['active_connections']
                print(f"Time {i+1}s | Active Connections: {active}")
            except Exception as e:
                print(f"Error fetching stats: {e}")
            await asyncio.sleep(0.5)

async def main():
    print("🚀 Demo boshlanmoqda...")
    print(f"Maqsad: {NUM_REQUESTS} ta so'rov yuborish va real vaqtda serverlardagi ulanishlarni ko'rish.\n")
    
    # Start monitoring and sending requests
    # We use a slight delay before sending requests so we can catch the 'zero' state too
    monitor_task = asyncio.create_task(monitor_stats())
    await asyncio.sleep(0.2)
    
    request_task = asyncio.create_task(send_requests())
    
    await asyncio.gather(monitor_task, request_task)
    print("\n✅ Demo yakunlandi.")

if __name__ == "__main__":
    asyncio.run(main())
