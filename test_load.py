import asyncio
import httpx
from collections import Counter
import time

# Load Balancer manzili
URL = "http://127.0.0.1:8000/"
# Test uchun so'rovlar soni
NUM_REQUESTS = 60

async def call_balancer(client):
    try:
        response = await client.get(URL, timeout=5.0)
        data = response.json()
        return data.get("service", "Error")
    except Exception as e:
        return f"Error: {e}"

async def main():
    print(f"🚀 Load Test boshlanmoqda: {NUM_REQUESTS} ta so'rov yuborilmoqda...")
    print(f"📍 Manzil: {URL}\n")
    
    async with httpx.AsyncClient() as client:
        # Barcha so'rovlarni parallel yuboramiz
        tasks = [call_balancer(client) for _ in range(NUM_REQUESTS)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
    # Natijalarni sanaymiz
    counts = Counter(results)
    
    print("📊 --- Yuk taqsimlanishi natijalari ---")
    for service, count in sorted(counts.items()):
        percentage = (count / NUM_REQUESTS) * 100
        print(f"| {service:15} | {count:3} ta so'rov | {percentage:5.1f}% |")
    
    print("-" * 45)
    print(f"⏱ Umumiy vaqt: {end_time - start_time:.2f} soniya")
    print(f"⚡️ Tezlik: {NUM_REQUESTS / (end_time - start_time):.2f} so'rov/sek")
    print("-" * 45)

if __name__ == "__main__":
    asyncio.run(main())
