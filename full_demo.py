import subprocess
import time
import httpx
import asyncio
import os
import sys

# Absolute paths to ensure it runs correctly in any environment
VENV_PATH = "/Users/macbook/BMI/microservice_demo/.venv/bin"
UVICORN_BIN = f"{VENV_PATH}/uvicorn"
PYTHON_BIN = f"{VENV_PATH}/python"

# Limits to avoid PoolTimeout
LIMITS = httpx.Limits(max_connections=1200, max_keepalive_connections=200)

async def send_requests(url):
    print(f"🚀 1000 ta so'rov yuborilyapti...", flush=True)
    async with httpx.AsyncClient(limits=LIMITS, timeout=60.0) as client:
        tasks = [client.get(url) for _ in range(1000)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"✅ 1000 ta so'rov yakunlandi. (Errors: {len([r for r in results if isinstance(r, Exception)])})", flush=True)

async def check_stats(url):
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(15): # Check stats for longer
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    active = data['details']['active_connections']
                    print(f"⏱ Vaqt: {i*1.0}s | Serverlardagi yuk (Active Connections):", flush=True)
                    for s, count in active.items():
                        print(f"   - {s}: {count}", flush=True)
            except Exception as e:
                # print(f"Monitoring error: {e}", flush=True)
                pass
            await asyncio.sleep(1.0)

async def start_demo():
    processes = []
    try:
        # Start services
        print("🛠 Servislar ishga tushirilmoqda...", flush=True)
        for i in range(1, 4):
            p = subprocess.Popen(
                [UVICORN_BIN, f"service_{i}.main:app", "--host", "127.0.0.1", "--port", str(8000+i)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            processes.append(p)
        
        # Start LB
        lb = subprocess.Popen(
            [UVICORN_BIN, "load_balancer.main:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        processes.append(lb)
        
        print("⏳ Servislar tayyor bo'lishini kutyapmiz (7 soniya)...", flush=True)
        await asyncio.sleep(7) 
        
        # Run demo tasks concurrently
        print("🏁 Demo boshlandi!", flush=True)
        # Start stats checker as a background task
        stats_checker = asyncio.create_task(check_stats("http://127.0.0.1:8000/stats"))
        
        await asyncio.sleep(0.5)
        # Send load
        await send_requests("http://127.0.0.1:8000/")
        
        # Wait for stats checker to finish
        await stats_checker
        
    finally:
        print("\n🧹 Tozalash (servislarni o'chirish)...", flush=True)
        for p in processes:
            try:
                p.terminate()
            except:
                pass

if __name__ == "__main__":
    try:
        asyncio.run(start_demo())
    except KeyboardInterrupt:
        pass
